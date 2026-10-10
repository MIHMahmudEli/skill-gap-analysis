"""Dependency-aware experiment scheduler / watchdog for Kaggle GPU kernels.

Registry states: PENDING -> RUNNING -> COMPLETED -> VERIFIED
                 (plus FAILED / RETRY)

The scheduler assigns one experiment per idle worker (round-robin over the
16 credentials in .env), pushes a GPU kernel bound to the staged input
dataset, polls for completion, downloads outputs into results/<exp_id>/,
and retries transient failures (max 2 retries, different worker).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (KAGGLE_INPUT_DATASET, REGISTRY_PATH, RESULTS_DIR,
                    parse_env_workers, read_json, utc_now, write_json)
from kaggle_client import KaggleWorker, build_kernel_folder

EXP_SCRIPTS_DIR = Path(__file__).resolve().parent / "exp_scripts"
KERNEL_BUILD_DIR = RESULTS_DIR / "_kernels"
POLL_SEC = 25
MAX_ATTEMPTS = 3
MAX_STATUS_ERRORS = 6          # circuit breaker: consecutive poll failures
POST_PUSH_VERIFY_DELAY = 20    # seconds to wait before confirming a kernel exists

EXPERIMENTS = [
    {"exp_id": "ALIGN01_lexical_bootstrap", "slug": "sg-align01-lexical",
     "script": "align01_lexical.py", "deps": [], "internet": False},
    {"exp_id": "ALIGN02_semantic_sbert", "slug": "sg-align02-semantic",
     "script": "align02_semantic.py", "deps": [], "internet": True},
    {"exp_id": "ALIGN03_domain_gap", "slug": "sg-align03-domaingap",
     "script": "align03_domain_gap.py", "deps": [], "internet": True},
    {"exp_id": "STAT01_placement_core", "slug": "sg-stat01-placement",
     "script": "stat01_placement_core.py", "deps": [], "internet": False},
    {"exp_id": "STAT02_external_validation", "slug": "sg-stat02-external",
     "script": "stat02_external_valid.py", "deps": [], "internet": False},
    {"exp_id": "GEO01_linkedin_shares", "slug": "sg-geo01-linkedin",
     "script": "geo01_linkedin.py", "deps": [], "internet": False},
    {"exp_id": "TRENDS01_ai_longitudinal", "slug": "sg-trends01-ai",
     "script": "trends01_ai.py", "deps": [], "internet": False},
    {"exp_id": "INTL01_internship_effect", "slug": "sg-intl01-internship",
     "script": "intl01_internship.py", "deps": [], "internet": False},
    {"exp_id": "PLAC01_global_by_country", "slug": "sg-plac01-global",
     "script": "plac01_global_country.py", "deps": [], "internet": False},
]


def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        return read_json(REGISTRY_PATH)
    reg = {
        "created_utc": utc_now(),
        "input_dataset": KAGGLE_INPUT_DATASET,
        "experiments": {
            e["exp_id"]: {
                "status": "PENDING",
                "slug": e["slug"],
                "deps": e["deps"],
                "attempts": 0,
                "worker": None,
                "kernel_ref": None,
                "history": [],
            }
            for e in EXPERIMENTS
        },
    }
    return reg


def save_registry(reg: dict) -> None:
    write_json(REGISTRY_PATH, reg)


def deps_satisfied(reg: dict, exp: dict) -> bool:
    return all(
        reg["experiments"][d]["status"] in ("COMPLETED", "VERIFIED")
        for d in exp["deps"]
    )


def pick_worker(workers, busy: set, idx_counter: list) -> KaggleWorker:
    for w in workers:
        if w.username not in busy:
            busy.add(w.username)
            return w
    # all busy: round-robin anyway (Kaggle allows concurrent kernels)
    w = workers[idx_counter[0] % len(workers)]
    idx_counter[0] += 1
    busy.add(w.username)
    return w


def main() -> None:
    # Single-account mode (user-requested): run everything under one Kaggle
    # account for easy tracking. Falls back to all 16 if that account is
    # missing from .env.
    all_workers = parse_env_workers()
    preferred = os.environ.get("SKILLGAP_WORKER", "nihanshadman")
    workers = [w for w in all_workers if w["username"] == preferred] or all_workers
    print(f"Using worker pool: {[w['username'] for w in workers]} "
          f"(of {len(all_workers)} configured)", flush=True)
    kworkers = [KaggleWorker(w["username"], w["token"], i)
                for i, w in enumerate(workers)]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    reg = load_registry()
    save_registry(reg)

    busy: set = set()
    running: dict = {}  # exp_id -> {"worker": KaggleWorker, "kernel_ref": str}

    def attempt_push(exp_id: str) -> None:
        spec = next(e for e in EXPERIMENTS if e["exp_id"] == exp_id)
        entry = reg["experiments"][exp_id]
        if entry["attempts"] >= MAX_ATTEMPTS:
            entry["status"] = "FAILED"
            entry["history"].append({"ts": utc_now(), "event": "max_attempts_exhausted"})
            return
        entry["attempts"] += 1
        worker = pick_worker(kworkers, busy, [0])
        slug = f"{spec['slug']}-a{entry['attempts']}"
        kernel_dir = build_kernel_folder(
            KERNEL_BUILD_DIR / slug, worker, slug,
            EXP_SCRIPTS_DIR / spec["script"],
            dataset_sources=[KAGGLE_INPUT_DATASET],
            enable_gpu=True, enable_internet=spec["internet"],
        )
        print(f"[{utc_now()}] PUSH {exp_id} -> {worker.username}/{slug} "
              f"(attempt {entry['attempts']})", flush=True)
        try:
            worker.kernels_push(kernel_dir, accelerator="GPU", timeout=7200)
        except Exception as e:
            entry["history"].append({"ts": utc_now(), "event": "push_failed",
                                     "error": str(e)[:500]})
            busy.discard(worker.username)
            print(f"  PUSH FAILED: {e}", flush=True)
            return
        # Verify the kernel actually exists before declaring RUNNING.
        time.sleep(POST_PUSH_VERIFY_DELAY)
        try:
            info = worker.kernels_status(f"{worker.username}/{slug}")
            entry["history"].append({"ts": utc_now(), "event": "push_verified",
                                     "first_state": info})
        except Exception as e:
            entry["history"].append({"ts": utc_now(), "event": "push_unverified",
                                     "error": str(e)[:400]})
            busy.discard(worker.username)
            print(f"  PUSH UNVERIFIED: {e}", flush=True)
            return
        entry["status"] = "RUNNING"
        entry["worker"] = worker.username
        entry["kernel_ref"] = f"{worker.username}/{slug}"
        entry["pushed_utc"] = utc_now()
        entry["history"].append({"ts": utc_now(), "event": "pushed",
                                 "kernel_ref": entry["kernel_ref"]})
        entry["status_errors"] = 0
        running[exp_id] = {"worker": worker, "kernel_ref": entry["kernel_ref"]}
        save_registry(reg)

    idle_rounds = 0
    while True:
        reg = load_registry()
        statuses = {eid: e["status"] for eid, e in reg["experiments"].items()}

        # 1. Assign pending experiments whose deps are satisfied.
        for exp in EXPERIMENTS:
            eid = exp["exp_id"]
            if (statuses.get(eid) == "PENDING" and deps_satisfied(reg, exp)
                    and eid not in running):
                attempt_push(eid)

        # 2. Poll running kernels.
        for exp_id, info in list(running.items()):
            entry = reg["experiments"][exp_id]
            try:
                state = info["worker"].kernels_status(info["kernel_ref"])
                entry["status_errors"] = 0
            except Exception as e:
                entry["status_errors"] = entry.get("status_errors", 0) + 1
                entry["history"].append({"ts": utc_now(),
                                         "event": "status_error",
                                         "error": str(e)[:300],
                                         "consecutive": entry["status_errors"]})
                print(f"[{utc_now()}] STATUS-ERR {exp_id} "
                      f"({entry['status_errors']}/{MAX_STATUS_ERRORS}): {e}",
                      flush=True)
                if entry["status_errors"] >= MAX_STATUS_ERRORS:
                    entry["status"] = ("RETRY" if entry["attempts"] < MAX_ATTEMPTS
                                       else "FAILED")
                    entry["history"].append({"ts": utc_now(),
                                             "event": "circuit_breaker_open"})
                    del running[exp_id]
                    busy.discard(info["worker"].username)
                    print(f"  CIRCUIT BREAKER {exp_id} -> {entry['status']}",
                          flush=True)
                save_registry(reg)
                continue
            entry["last_state"] = state
            print(f"[{utc_now()}] POLL {exp_id} ({info['kernel_ref']}): {state}",
                  flush=True)
            if state == "complete":
                dest = RESULTS_DIR / exp_id
                if dest.exists():
                    shutil.rmtree(dest)
                try:
                    info["worker"].kernels_output(info["kernel_ref"], dest)
                except Exception as e:
                    entry["history"].append({"ts": utc_now(),
                                             "event": "download_failed",
                                             "error": str(e)[:500]})
                    entry["status"] = "RETRY"
                    del running[exp_id]
                    busy.discard(info["worker"].username)
                    save_registry(reg)
                    continue
                has_metrics = (dest / "metrics.json").exists()
                entry["history"].append({"ts": utc_now(),
                                         "event": "downloaded",
                                         "metrics_json": has_metrics})
                if has_metrics:
                    entry["status"] = "COMPLETED"
                    entry["completed_utc"] = utc_now()
                    print(f"  DONE {exp_id} -> {dest}")
                else:
                    entry["status"] = "FAILED"
                    entry["history"].append({"ts": utc_now(),
                                             "event": "missing_metrics_json"})
                    log_tail = info["worker"].kernels_logs_tail(info["kernel_ref"])
                    (dest / "kernels_logs_tail.txt").write_text(log_tail,
                                                                encoding="utf-8")
                    print(f"  FAILED {exp_id}: no metrics.json (logs saved)")
                del running[exp_id]
                busy.discard(info["worker"].username)
                save_registry(reg)
            elif state in ("failed", "cancelled", "error"):
                entry["status"] = "RETRY" if entry["attempts"] < MAX_ATTEMPTS else "FAILED"
                entry["history"].append({"ts": utc_now(), "event": f"kernel_{state}"})
                log_tail = info["worker"].kernels_logs_tail(info["kernel_ref"])
                dest = RESULTS_DIR / f"{exp_id}_attempt{entry['attempts']}"
                dest.mkdir(parents=True, exist_ok=True)
                (dest / "kernels_logs_tail.txt").write_text(log_tail, encoding="utf-8")
                del running[exp_id]
                busy.discard(info["worker"].username)
                save_registry(reg)
                print(f"  KERNEL {state.upper()} {exp_id} "
                      f"({'retry' if entry['status'] == 'RETRY' else 'give up'})")

        # 3. Re-queue RETRY entries.
        for exp in EXPERIMENTS:
            eid = exp["exp_id"]
            if reg["experiments"][eid]["status"] == "RETRY" and eid not in running:
                reg["experiments"][eid]["status"] = "PENDING"
                reg["experiments"][eid]["status_errors"] = 0
                save_registry(reg)

        # 4. Termination check.
        statuses = {e["status"] for e in reg["experiments"].values()}
        if not running and statuses <= {"COMPLETED", "VERIFIED", "FAILED"}:
            break
        if not running and statuses == {"PENDING"}:
            idle_rounds += 1
            if idle_rounds > 3:
                print("No progress possible; aborting.")
                break
        time.sleep(POLL_SEC if running else 5)

    print("\n==== FINAL REGISTRY ====")
    for eid, e in reg["experiments"].items():
        print(f"{eid:32s} {e['status']:10s} attempts={e['attempts']} "
              f"worker={e['worker']} ref={e['kernel_ref']}")
    save_registry(reg)


if __name__ == "__main__":
    main()
