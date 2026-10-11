"""Dependency-aware experiment scheduler / watchdog for Kaggle GPU kernels.

Registry states: PENDING -> RUNNING -> COMPLETED -> VERIFIED
                 (plus FAILED / RETRY)

Design notes
------------
* Full 16-worker pool from .env (user-authorized parallelism).
* Parallel candidates: if a pushed kernel stays QUEUED longer than
  QUEUE_PARALLEL_AFTER seconds, the SAME experiment is additionally pushed
  on other workers (up to MAX_PARALLEL racing kernels, MAX_ATTEMPTS total
  pushes). First candidate to reach `complete` wins; its outputs are
  downloaded and the remaining duplicates are recorded as abandoned.
* Resumable: registry entries stuck in RUNNING are re-adopted on startup
  from their last kernel_ref, so an aborted scheduler can be restarted.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (KAGGLE_INPUT_DATASET, REGISTRY_PATH, RESULTS_DIR,
                    parse_env_workers, read_json, utc_now, write_json)
from kaggle_client import KaggleWorker, build_kernel_folder

EXP_SCRIPTS_DIR = Path(__file__).resolve().parent / "exp_scripts"
KERNEL_BUILD_DIR = RESULTS_DIR / "_kernels"
POLL_SEC = 25
MAX_ATTEMPTS = 5           # total pushes per experiment
MAX_PARALLEL = 4           # racing kernels per experiment
QUEUE_PARALLEL_AFTER = 480  # seconds queued before adding a parallel push
MAX_STATUS_ERRORS = 6       # circuit breaker: consecutive poll failures
POST_PUSH_VERIFY_DELAY = 20  # seconds before confirming a kernel exists

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
    {"exp_id": "VALID01_esco_gold", "slug": "sg-valid01-gold",
     "script": "valid01_esco_gold.py", "deps": [], "internet": True},
    {"exp_id": "ALIGN04_crosscorpus_linkedin", "slug": "sg-align04-crosscorpus",
     "script": "align04_crosscorpus.py", "deps": [], "internet": True},
    {"exp_id": "CURR01_cs2023_anchor", "slug": "sg-curr01-cs2023",
     "script": "curr01_cs2023_anchor.py", "deps": [], "internet": True},
]


def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        reg = read_json(REGISTRY_PATH)
        for e in EXPERIMENTS:
            reg["experiments"].setdefault(e["exp_id"], {
                "status": "PENDING",
                "slug": e["slug"],
                "deps": e["deps"],
                "attempts": 0,
                "worker": None,
                "kernel_ref": None,
                "history": [],
            })
        return reg
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


def parse_ts(s: str) -> float:
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc).timestamp()
    except Exception:
        return time.time()


def main() -> None:
    all_workers = parse_env_workers()
    # de-duplicate by username, keep order
    seen, uniq = set(), []
    for w in all_workers:
        if w["username"] not in seen:
            seen.add(w["username"])
            uniq.append(w)
    kworkers = {w["username"]: KaggleWorker(w["username"], w["token"], i)
                for i, w in enumerate(uniq)}
    pool = list(kworkers.values())
    print(f"Worker pool ({len(pool)}): {[w.username for w in pool]}",
          flush=True)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    reg = load_registry()
    save_registry(reg)

    busy: set = set()                       # usernames hosting live candidates
    running: dict = {}                      # exp_id -> {"candidates": [...]}

    def candidate_busy_names(exp_id: str) -> set:
        return {c["worker"].username
                for c in running.get(exp_id, {}).get("candidates", [])}

    def push_candidate(exp_id: str) -> bool:
        spec = next(e for e in EXPERIMENTS if e["exp_id"] == exp_id)
        entry = reg["experiments"][exp_id]
        if entry["attempts"] >= MAX_ATTEMPTS:
            return False
        free = [w for w in pool
                if w.username not in busy
                and w.username not in candidate_busy_names(exp_id)]
        if not free:
            return False
        worker = free[0]
        n = entry["attempts"] + 1
        slug = f"{spec['slug']}-a{n}"
        kernel_dir = build_kernel_folder(
            KERNEL_BUILD_DIR / slug, worker, slug,
            EXP_SCRIPTS_DIR / spec["script"],
            dataset_sources=[KAGGLE_INPUT_DATASET],
            enable_gpu=True, enable_internet=spec["internet"],
        )
        print(f"[{utc_now()}] PUSH {exp_id} -> {worker.username}/{slug} "
              f"(attempt {n})", flush=True)
        try:
            worker.kernels_push(kernel_dir, accelerator="GPU", timeout=7200)
        except Exception as e:
            entry["history"].append({"ts": utc_now(), "event": "push_failed",
                                     "error": str(e)[:500]})
            print(f"  PUSH FAILED: {e}", flush=True)
            return False
        time.sleep(POST_PUSH_VERIFY_DELAY)
        ref = f"{worker.username}/{slug}"
        try:
            info = worker.kernels_status(ref)
            entry["history"].append({"ts": utc_now(), "event": "push_verified",
                                     "kernel_ref": ref, "first_state": info})
        except Exception as e:
            entry["history"].append({"ts": utc_now(),
                                     "event": "push_unverified",
                                     "kernel_ref": ref, "error": str(e)[:400]})
            print(f"  PUSH UNVERIFIED: {e}", flush=True)
            return False
        entry["attempts"] = n
        entry["status"] = "RUNNING"
        entry["worker"] = worker.username
        entry["kernel_ref"] = ref
        entry["pushed_utc"] = utc_now()
        entry["status_errors"] = 0
        entry["history"].append({"ts": utc_now(), "event": "pushed",
                                 "kernel_ref": ref})
        busy.add(worker.username)
        running.setdefault(exp_id, {"candidates": []})["candidates"].append(
            {"worker": worker, "kernel_ref": ref,
             "pushed_ts": time.time(), "attempt": n})
        save_registry(reg)
        return True

    # --- adopt RUNNING entries left behind by a previous scheduler run ----
    for exp in EXPERIMENTS:
        eid = exp["exp_id"]
        entry = reg["experiments"][eid]
        if entry.get("status") == "RUNNING" and entry.get("kernel_ref"):
            w = kworkers.get(entry.get("worker"))
            if w is None and "/" in entry["kernel_ref"]:
                w = kworkers.get(entry["kernel_ref"].split("/", 1)[0])
            if w is not None:
                busy.add(w.username)
                running.setdefault(eid, {"candidates": []})["candidates"].append(
                    {"worker": w, "kernel_ref": entry["kernel_ref"],
                     "pushed_ts": parse_ts(entry.get("pushed_utc", "")),
                     "attempt": entry.get("attempts", 1)})
                print(f"[{utc_now()}] ADOPT {eid} -> {entry['kernel_ref']}",
                      flush=True)
            else:
                entry["status"] = "RETRY"
                entry["history"].append({"ts": utc_now(),
                                         "event": "adoption_failed"})
                save_registry(reg)

    def finish_exp(exp_id: str, winner: dict, dest: Path, ok: bool) -> None:
        entry = reg["experiments"][exp_id]
        cands = running.get(exp_id, {}).get("candidates", [])
        for c in cands:
            busy.discard(c["worker"].username)
            if c["kernel_ref"] != winner["kernel_ref"]:
                entry["history"].append(
                    {"ts": utc_now(), "event": "abandoned_duplicate",
                     "kernel_ref": c["kernel_ref"]})
        entry["worker"] = winner["worker"].username
        entry["kernel_ref"] = winner["kernel_ref"]
        running.pop(exp_id, None)
        save_registry(reg)

    idle_rounds = 0
    while True:
        reg = load_registry()
        statuses = {eid: e["status"] for eid, e in reg["experiments"].items()}

        # 1. First push for pending experiments with satisfied deps.
        for exp in EXPERIMENTS:
            eid = exp["exp_id"]
            if (statuses.get(eid) == "PENDING" and deps_satisfied(reg, exp)
                    and eid not in running):
                if not push_candidate(eid):
                    if reg["experiments"][eid]["attempts"] >= MAX_ATTEMPTS:
                        reg["experiments"][eid]["status"] = "FAILED"
                        reg["experiments"][eid]["history"].append(
                            {"ts": utc_now(),
                             "event": "max_attempts_exhausted"})
                        save_registry(reg)

        # 2. Poll all candidates of running experiments.
        for exp_id in list(running):
            entry = reg["experiments"][exp_id]
            cands = running[exp_id]["candidates"]
            winner = None
            fatal = False
            for c in list(cands):
                try:
                    state = c["worker"].kernels_status(c["kernel_ref"])
                except Exception as e:
                    entry["status_errors"] = entry.get("status_errors", 0) + 1
                    entry["history"].append(
                        {"ts": utc_now(), "event": "status_error",
                         "error": str(e)[:300],
                         "consecutive": entry["status_errors"]})
                    print(f"[{utc_now()}] STATUS-ERR {exp_id} "
                          f"({entry['status_errors']}/{MAX_STATUS_ERRORS}): {e}",
                          flush=True)
                    if entry["status_errors"] >= MAX_STATUS_ERRORS:
                        fatal = True
                    continue
                entry["status_errors"] = 0
                print(f"[{utc_now()}] POLL {exp_id} ({c['kernel_ref']}): "
                      f"{state}", flush=True)
                if state == "complete":
                    winner = c
                elif state in ("failed", "cancelled", "error"):
                    entry["history"].append(
                        {"ts": utc_now(), "event": f"kernel_{state}",
                         "kernel_ref": c["kernel_ref"]})
                    try:
                        log_tail = c["worker"].kernels_logs_tail(
                            c["kernel_ref"])
                        d = RESULTS_DIR / (
                            f"{exp_id}_attempt{c.get('attempt', 0)}")
                        d.mkdir(parents=True, exist_ok=True)
                        (d / "kernels_logs_tail.txt").write_text(
                            log_tail, encoding="utf-8")
                    except Exception:
                        pass
                    busy.discard(c["worker"].username)
                    cands.remove(c)
                    print(f"  KERNEL {state.upper()} {exp_id} "
                          f"({c['kernel_ref']}) removed", flush=True)
                elif state == "pending":
                    # queued too long -> add a parallel attempt elsewhere
                    if (len(cands) < MAX_PARALLEL
                            and entry["attempts"] < MAX_ATTEMPTS
                            and time.time() - c["pushed_ts"]
                            > QUEUE_PARALLEL_AFTER):
                        print(f"  QUEUED> {QUEUE_PARALLEL_AFTER}s for "
                              f"{c['kernel_ref']}; pushing parallel "
                              f"candidate...", flush=True)
                        push_candidate(exp_id)
                        cands = running[exp_id]["candidates"]

            if fatal:
                entry["status"] = ("RETRY"
                                   if entry["attempts"] < MAX_ATTEMPTS
                                   else "FAILED")
                entry["history"].append(
                    {"ts": utc_now(), "event": "circuit_breaker_open"})
                for c in cands:
                    busy.discard(c["worker"].username)
                running.pop(exp_id, None)
                save_registry(reg)
                print(f"  CIRCUIT BREAKER {exp_id} -> {entry['status']}",
                      flush=True)
                continue

            if winner is not None:
                dest = RESULTS_DIR / exp_id
                if dest.exists():
                    shutil.rmtree(dest)
                try:
                    winner["worker"].kernels_output(winner["kernel_ref"], dest)
                except Exception as e:
                    entry["history"].append(
                        {"ts": utc_now(), "event": "download_failed",
                         "error": str(e)[:500]})
                    # drop the winner, keep any remaining candidates
                    busy.discard(winner["worker"].username)
                    cands.remove(winner)
                    if not cands:
                        entry["status"] = "RETRY"
                        running.pop(exp_id, None)
                    save_registry(reg)
                    continue
                has_metrics = (dest / "metrics.json").exists()
                entry["history"].append(
                    {"ts": utc_now(), "event": "downloaded",
                     "kernel_ref": winner["kernel_ref"],
                     "metrics_json": has_metrics})
                if has_metrics:
                    entry["status"] = "COMPLETED"
                    entry["completed_utc"] = utc_now()
                    finish_exp(exp_id, winner, dest, True)
                    print(f"  DONE {exp_id} <- {winner['kernel_ref']} -> {dest}")
                else:
                    entry["status"] = "FAILED"
                    entry["history"].append(
                        {"ts": utc_now(), "event": "missing_metrics_json"})
                    try:
                        log_tail = winner["worker"].kernels_logs_tail(
                            winner["kernel_ref"])
                        (dest / "kernels_logs_tail.txt").write_text(
                            log_tail, encoding="utf-8")
                    except Exception:
                        pass
                    finish_exp(exp_id, winner, dest, False)
                    print(f"  FAILED {exp_id}: no metrics.json (logs saved)")
            elif not cands:
                # all candidates died this round
                entry["status"] = ("RETRY"
                                   if entry["attempts"] < MAX_ATTEMPTS
                                   else "FAILED")
                running.pop(exp_id, None)
                save_registry(reg)
                print(f"  {exp_id} -> {entry['status']} (no candidates left)")

        # 3. Re-queue RETRY entries.
        for exp in EXPERIMENTS:
            eid = exp["exp_id"]
            if (reg["experiments"][eid]["status"] == "RETRY"
                    and eid not in running):
                reg["experiments"][eid]["status"] = "PENDING"
                reg["experiments"][eid]["status_errors"] = 0
                save_registry(reg)

        # 4. Termination check.
        statuses = {e["status"] for e in reg["experiments"].values()}
        terminal = {"COMPLETED", "VERIFIED", "FAILED", "USED_IN_MANUSCRIPT"}
        if not running and statuses <= terminal:
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
