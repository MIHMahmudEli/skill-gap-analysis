#!/usr/bin/env python3
"""Verify the 5 CPU-blocked embedding experiments on a Kaggle CPU kernel.

The 5 embedding experiments (ALIGN02, ALIGN03, ALIGN04, CURR01, VALID01) could
not be executed on the author's machine because WDAC/AppTracker blocks
``torch._C`` and ``statsmodels``.  This driver pushes them to a *CPU-only*
Kaggle kernel owned by the single account that owns the input bundle
(``studyhub991`` -- never rotates across the other workers in .env), polls the
run, downloads the output and gates it against the committed artifacts.

    python scripts/kaggle_cpu_verify.py build     # assemble the kernel folder
    python scripts/kaggle_cpu_verify.py run       # push, poll, download
    python scripts/kaggle_cpu_verify.py gate      # compare + headline gate
    python scripts/kaggle_cpu_verify.py upload    # HF upload (allowlisted)
    python scripts/kaggle_cpu_verify.py all       # everything, in order

Staging lives in ``.kaggle_cpu_verify/`` (gitignored).  Downloaded artifacts
are normalised into ``results_cpu_kaggle/`` (committed).

Credentials are read from .env and are never printed, logged or written to any
file that leaves this machine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "scripts"))

from common import ENV_PATH, parse_env_workers  # noqa: E402
from kaggle_client import KaggleWorker, build_kernel_folder  # noqa: E402
import compare_cpu_results as ccr  # noqa: E402  (shared tolerance + exclusions)

STAGE = ROOT / ".kaggle_cpu_verify"
KERNEL_DIR = STAGE / "kernel"
OUTPUT_DIR = STAGE / "output"
LOG_DIR = STAGE / "logs"
CPU_DIR = ROOT / "results_cpu_kaggle"
REF_DIR = ROOT / "results"
REPORT = ROOT / "reports" / "CPU_VS_COMMITTED_KAGGLE.md"
GATE_JSON = ROOT / "reports" / "cpu_kaggle_gate.json"

# The one account that owns the input dataset.  Never rotate.
OWNER = "studyhub991"
INPUT_DATASET = f"{OWNER}/skill-gap-inputs-v1"
SLUG = "cpu-verify-embedding-5"

# Public repository the kernel clones.  Kaggle's CLI uploads only the kernel's
# code_file, so the code has to arrive over the internet; the kernel then
# asserts the clone's HEAD equals the commit pinned at build time.
REPO_URL = "https://github.com/MIHMahmudEli/skill-gap-analysis.git"

EXPERIMENTS = [
    "ALIGN02_semantic_sbert",
    "ALIGN03_domain_gap",
    "ALIGN04_crosscorpus_linkedin",
    "CURR01_cs2023_anchor",
    "VALID01_esco_gold",
]

POLL_INTERVAL = 30
POLL_MAX_SECONDS = 3 * 3600
PUSH_TIMEOUT = 10800

# ---------------------------------------------------------------------------
# Headline gate.
#
# "Reported precision" is the number of decimals the manuscript (and therefore
# audit/verify_claims.py) prints for each headline number:
#   * percentages printed to 1 dp  -> round the fraction to 3 dp
#   * ratios printed to 3 dp       -> round to 3 dp
#   * percentage-point gaps printed to 2 dp -> round to 2 dp
# A headline field passes only when round(kaggle, d) == round(committed, d).
# ---------------------------------------------------------------------------
HEADLINE = {
    "ALIGN02_semantic_sbert": [
        ("sgi_at_tau_0.5", 3),
        ("sgi_ci_at_tau_0.5[0]", 3),
        ("sgi_ci_at_tau_0.5[1]", 3),
        ("sensitivity[*].SGI", 3),
        ("sensitivity[*].CI_Lower", 3),
        ("sensitivity[*].CI_Upper", 3),
    ],
    "ALIGN03_domain_gap": [
        ("domain_gaps[*].deficit_pp_lexical", 2),
        ("domain_gaps[*].deficit_pp_semantic", 2),
        ("domain_gaps[*].deficit_lex_ci_lower", 2),
        ("domain_gaps[*].deficit_lex_ci_upper", 2),
        ("domain_gaps[*].deficit_sem_ci_lower", 2),
        ("domain_gaps[*].deficit_sem_ci_upper", 2),
    ],
    "ALIGN04_crosscorpus_linkedin": [
        ("lexical_sgi", 3),
        ("lexical_sgi_ci[0]", 3),
        ("lexical_sgi_ci[1]", 3),
        ("semantic_sgi_tau_0.5", 3),
        ("semantic_sgi_tau_0.5_ci[0]", 3),
        ("semantic_sgi_tau_0.5_ci[1]", 3),
    ],
    "CURR01_cs2023_anchor": [
        ("overall_coverage_sem_tau_0.5", 3),
        ("reverse_coverage_academic_tau_0.5", 3),
        ("sensitivity[*].overall_coverage_semantic", 3),
        ("sensitivity[*].CI_Lower", 3),
        ("sensitivity[*].CI_Upper", 3),
        ("per_ka[*].coverage_sem_tau_0.5", 3),
    ],
    "VALID01_esco_gold": [
        ("kappa_at_tau_0.5", 3),
        ("kappa_ci_at_tau_0.5[0]", 3),
        ("kappa_ci_at_tau_0.5[1]", 3),
        ("precision_at_tau_0.5", 3),
        ("recall_at_tau_0.5", 3),
        ("accuracy_at_tau_0.5", 3),
        ("auc_cosine", 3),
        ("kappa_lexical_exact", 3),
        ("kappa_lexical_contains", 3),
        ("esco_coverage[*].semantic_coverage_tau0.5", 2),
        ("esco_coverage[*].lexical_coverage", 2),
    ],
}

# ---------------------------------------------------------------------------
# Kernel payload (generated verbatim; __TOKENS__ are substituted at build).
# ---------------------------------------------------------------------------
KERNEL_SCRIPT = r'''#!/usr/bin/env python3
"""Kaggle CPU verification of the 5 CPU-blocked embedding experiments.

GENERATED by scripts/kaggle_cpu_verify.py -- do not edit by hand.
"""
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

EXPERIMENTS = __EXPERIMENTS__
EXPECTED_COMMIT = "__COMMIT__"
ARCHIVE_SHA256 = "__ARCHIVE_SHA256__"
INPUT_DATASET = "__INPUT_DATASET__"
REPO_URL = "__REPO_URL__"

WORK = Path("/kaggle/working")
HERE = Path(__file__).resolve().parent
LOG_DIR = WORK / "kaggle_cpu_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_lines = []


def log(msg=""):
    msg = str(msg)
    print(msg, flush=True)
    _lines.append(msg)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --- deterministic execution environment, set BEFORE numpy/torch import ---
for _k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_k] = "1"
os.environ["PYTHONHASHSEED"] = "42"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
# fail fast on a git prompt instead of hanging the kernel for an hour
os.environ["GIT_TERMINAL_PROMPT"] = "0"
os.environ["GIT_ASKPASS"] = "echo"

started = time.time()
run_info = {
    "commit": EXPECTED_COMMIT,
    "repo_archive_sha256": ARCHIVE_SHA256,
    "input_dataset": INPUT_DATASET,
    "seed": 42,
    "single_thread_blas": True,
    "experiments_requested": EXPERIMENTS,
}


def fatal(msg):
    log("FATAL: " + str(msg))
    run_info["status"] = "fatal"
    run_info["fatal"] = str(msg)
    run_info["total_runtime_sec"] = round(time.time() - started, 1)
    (WORK / "run_info.json").write_text(json.dumps(run_info, indent=2),
                                        encoding="utf-8")
    (LOG_DIR / "kernel_log.txt").write_text("\n".join(_lines), encoding="utf-8")
    raise SystemExit(1)


# ---------------------------------------------------------------------------
# 1. materialise the repository at the exact commit that was pushed
#
# Kaggle's CLI uploads only the kernel's code_file, so a repo tarball cannot
# ride along in the kernel folder.  The repository is therefore cloned over
# the internet and then PINNED: the clone's HEAD must equal EXPECTED_COMMIT,
# and if it does not (because someone pushed since this kernel was built) the
# pinned commit is checked out explicitly and re-asserted.
# ---------------------------------------------------------------------------
def locate(name):
    for base in (HERE, WORK, Path.cwd()):
        p = base / name
        if p.exists():
            return p
    return None


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def materialise_repo():
    """Return (how, None) or (None, why).  Always leaves REPO at EXPECTED_COMMIT."""
    global REPO
    REPO = WORK / "repo"
    if REPO.exists():
        shutil.rmtree(REPO)

    r = _git("clone", "--quiet", REPO_URL, str(REPO))
    if r.returncode == 0:
        head = _git("-C", str(REPO), "rev-parse", "HEAD").stdout.strip()
        if head != EXPECTED_COMMIT:
            log("remote tip is %s; checking out the pinned %s"
                % (head[:12], EXPECTED_COMMIT[:12]))
            c = _git("-C", str(REPO), "checkout", "--quiet", EXPECTED_COMMIT)
            if c.returncode != 0:
                return None, ("clone HEAD %s and checkout of %s failed: %s"
                              % (head[:12], EXPECTED_COMMIT[:12],
                                 (c.stderr or "")[-400:]))
        head = _git("-C", str(REPO), "rev-parse", "HEAD").stdout.strip()
        if head != EXPECTED_COMMIT:
            return None, "checkout left HEAD at %s, expected %s" % (
                head, EXPECTED_COMMIT)
        if _git("-C", str(REPO), "status", "--porcelain").stdout.strip():
            return None, "cloned tree is not clean"
        return "git clone of " + REPO_URL, None

    # fallback, kept so the driver still works if extra files ever do ride along
    archive = locate("repo.tar.gz")
    if archive is not None:
        if sha256(archive) != ARCHIVE_SHA256:
            return None, ("repo archive sha256 mismatch: %s != %s"
                          % (sha256(archive), ARCHIVE_SHA256))
        with tarfile.open(archive) as tf:
            try:
                tf.extractall(REPO, filter="data")
            except TypeError:
                tf.extractall(REPO)
        return "shipped repo archive", None

    return None, ("git clone failed (rc=%d): %s"
                  % (r.returncode, (r.stderr or r.stdout or "")[-600:]))


_repo_source, _why = materialise_repo()
if _why:
    fatal(_why)
run_info["repo_source"] = _repo_source
log("repository at %s via %s" % (EXPECTED_COMMIT[:12], _repo_source))

# ---------------------------------------------------------------------------
# 2. pinned requirements
# ---------------------------------------------------------------------------
req = REPO / "requirements.txt"
pip_mode = "pinned"
r = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)],
                   capture_output=True, text=True)
(LOG_DIR / "pip_pinned.log").write_text(
    (r.stdout or "") + "\n--- stderr ---\n" + (r.stderr or ""), encoding="utf-8")
log("pip install -r requirements.txt -> rc=%d" % r.returncode)
if r.returncode != 0:
    keep = [ln for ln in req.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("kaggle==")]
    alt = REPO / "requirements_no_cli.txt"
    alt.write_text("\n".join(keep) + "\n", encoding="utf-8")
    r2 = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(alt)],
                        capture_output=True, text=True)
    (LOG_DIR / "pip_retry.log").write_text(
        (r2.stdout or "") + "\n--- stderr ---\n" + (r2.stderr or ""),
        encoding="utf-8")
    pip_mode = ("pinned" if r2.returncode == 0 else "pinned_failed")
    log("pip retry without the kaggle CLI pin -> rc=%d" % r2.returncode)
run_info["pip_mode"] = pip_mode

# ---------------------------------------------------------------------------
# 3. input bundle mount
# ---------------------------------------------------------------------------
detected = None
for cand in (Path("/kaggle/input/datasets") / INPUT_DATASET,
             Path("/kaggle/input") / INPUT_DATASET.split("/")[-1]):
    if cand.exists():
        detected = str(cand)
        break
if detected:
    os.environ["SKILLGAP_INPUT_DIR"] = detected
run_info["input_dir_detected"] = detected
log("input bundle at %s" % (detected or "NOT FOUND"))

# ---------------------------------------------------------------------------
# 4. run each experiment, one invocation each, so runtimes are per-experiment
# ---------------------------------------------------------------------------
results = {}
env = dict(os.environ)
for exp in EXPERIMENTS:
    log("=== %s ===" % exp)
    t0 = time.time()
    p = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "run_cpu_rerun.py"),
         "--only", exp],
        cwd=str(REPO), env=env, capture_output=True, text=True)
    dt = round(time.time() - t0, 1)
    (LOG_DIR / (exp + ".log")).write_text(
        (p.stdout or "") + "\n--- stderr ---\n" + (p.stderr or ""),
        encoding="utf-8")
    ok = p.returncode == 0
    results[exp] = {
        "runtime_sec": dt,
        "returncode": p.returncode,
        "status": "ok" if ok else "failed",
        "metrics_written": (REPO / "results_cpu" / exp / "metrics.json").exists(),
    }
    log("  %s  %.1fs  rc=%d" % ("OK  " if ok else "FAIL", dt, p.returncode))
run_info["experiments"] = results

# ---------------------------------------------------------------------------
# 5. environment report
# ---------------------------------------------------------------------------
def _ver(mod):
    try:
        m = __import__(mod)
        return str(getattr(m, "__version__", "unknown"))
    except Exception as e:  # pragma: no cover - diagnostic only
        return "unavailable (%s: %s)" % (type(e).__name__, e)


def _cpu_model():
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or platform.machine()


def _pycpu_count():
    try:
        return os.cpu_count()
    except Exception:
        return None


run_info.update({
    "python_version": sys.version.split()[0],
    "platform": platform.platform(),
    "cpu_model": _cpu_model(),
    "cpu_count": _pycpu_count(),
    "versions": {
        "numpy": _ver("numpy"),
        "pandas": _ver("pandas"),
        "scipy": _ver("scipy"),
        "scikit_learn": _ver("sklearn"),
        "torch": _ver("torch"),
        "sentence_transformers": _ver("sentence_transformers"),
    },
    "total_runtime_sec": round(time.time() - started, 1),
    "status": "ok" if all(v["status"] == "ok" for v in results.values())
              else "partial",
})

# ---------------------------------------------------------------------------
# 6. copy the results next to the run_info, then slim the downloadable output
# ---------------------------------------------------------------------------
src = REPO / "results_cpu"
dst = WORK / "results_cpu"
if dst.exists():
    shutil.rmtree(dst)
if src.exists():
    shutil.copytree(src, dst)
else:
    log("WARNING: no results_cpu/ produced")

(WORK / "run_info.json").write_text(json.dumps(run_info, indent=2, sort_keys=True),
                                    encoding="utf-8")
(LOG_DIR / "kernel_log.txt").write_text("\n".join(_lines), encoding="utf-8")

shutil.rmtree(REPO, ignore_errors=True)
for _p in (HERE / "repo.tar.gz", WORK / "repo.tar.gz",
           HERE / "repo_commit.txt", WORK / "repo_commit.txt"):
    try:
        _p.unlink()
    except Exception:
        pass

log("done status=%s total=%.1fs" % (run_info["status"],
                                    run_info["total_runtime_sec"]))
'''


# ---------------------------------------------------------------------------


def owner_worker() -> KaggleWorker:
    """The single account that owns the input bundle.  Never rotates."""
    workers = parse_env_workers(ENV_PATH)
    hit = [w for w in workers if w["username"] == OWNER]
    if not hit:
        raise SystemExit(
            f"FATAL: account '{OWNER}' (owner of {INPUT_DATASET}) is absent "
            f"from {ENV_PATH}. Refusing to fall back to another account.")
    return KaggleWorker(OWNER, hit[0]["token"], workers.index(hit[0]))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True,
                          text=True, check=True).stdout.strip()


def build_kernel(args=None) -> dict:
    head = git("rev-parse", "HEAD")
    commit = None
    if args is not None and getattr(args, "commit", None):
        commit = git("rev-parse", args.commit)
    else:
        # The kernel clones from GitHub, so pin the commit GitHub actually
        # serves -- not local HEAD, which may be ahead and unpushed.
        try:
            out = subprocess.run(["git", "ls-remote", "origin", "refs/heads/main"],
                                 cwd=str(ROOT), capture_output=True, text=True,
                                 timeout=120, check=True).stdout.split()
            commit = out[0] if out else None
        except Exception as e:
            print(f"WARNING: git ls-remote origin failed ({e}); "
                  f"falling back to local HEAD")
    if not commit:
        commit = head

    # The kernel runs committed experiment code; the paths it actually uses
    # must be identical between the pinned commit and the working tree.
    guarded = ["scripts/run_cpu_rerun.py", "experiments/exp_scripts",
               "experiments/common.py", "requirements.txt"]
    diff = git("diff", "--stat", commit, "HEAD", "--", *guarded).strip()
    extra = git("status", "--porcelain", "--", *guarded).strip()
    if diff or extra:
        print("FATAL: the experiment code differs between the pinned commit "
              f"{commit[:12]} and the working tree. Commit and push first, or "
              "re-run with --commit HEAD once the tree is clean.")
        if diff:
            print(diff)
        if extra:
            print(extra)
        raise SystemExit(1)
    if commit != head:
        print(f"NOTE: pinning the kernel to {commit[:12]} (what GitHub serves); "
              f"local HEAD is {head[:12]} and the guarded paths are identical.")

    STAGE.mkdir(parents=True, exist_ok=True)
    if KERNEL_DIR.exists():
        shutil.rmtree(KERNEL_DIR)

    script_path = STAGE / "_kernel_script.py"
    body = (KERNEL_SCRIPT
            .replace("__EXPERIMENTS__", json.dumps(EXPERIMENTS))
            .replace("__COMMIT__", commit)
            .replace("__ARCHIVE_SHA256__", "0" * 64)
            .replace("__INPUT_DATASET__", INPUT_DATASET)
            .replace("__REPO_URL__", REPO_URL))
    script_path.write_text(body, encoding="utf-8")

    worker = owner_worker()
    build_kernel_folder(KERNEL_DIR, worker, SLUG, script_path,
                        dataset_sources=[INPUT_DATASET],
                        enable_gpu=False, enable_internet=True)

    blob = subprocess.run(["git", "archive", "--format=tar", commit],
                          cwd=str(ROOT), capture_output=True, check=True).stdout
    info = {
        "commit": commit,
        "local_head": head,
        "commit_tree_sha256": hashlib.sha256(blob).hexdigest(),
        "commit_tree_bytes": len(blob),
        "repo_url": REPO_URL,
        "slug": f"{OWNER}/{SLUG}",
        "accelerator": "CPU",
        "enable_internet": True,
        "dataset_sources": [INPUT_DATASET],
        "files": sorted(p.name for p in KERNEL_DIR.iterdir() if p.is_file()),
    }
    (STAGE / "build_info.json").write_text(json.dumps(info, indent=2),
                                           encoding="utf-8")
    print("kernel folder : %s" % KERNEL_DIR)
    print("commit pinned : %s (local HEAD %s)" % (commit, head))
    print("repo url      : %s" % REPO_URL)
    print("slug          : %s" % info["slug"])
    print("accelerator   : CPU (enable_gpu=false, --accelerator omitted)")
    print("dataset source: %s" % INPUT_DATASET)
    print("files         : %s" % ", ".join(info["files"]))
    return info


def cmd_build(args) -> int:
    build_kernel(args)
    return 0


def cmd_run(args) -> int:
    # always rebuild: the pinned commit and the kernel script must be current
    build_kernel(args)
    worker = owner_worker()
    ref = f"{OWNER}/{SLUG}"

    if not args.skip_push:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\npushing {ref} (CPU, internet on, timeout {PUSH_TIMEOUT}s) ...")
        try:
            worker.kernels_push(KERNEL_DIR, accelerator=None,
                                timeout=PUSH_TIMEOUT)
        except Exception as e:
            print(f"push FAILED: {type(e).__name__}: {e}")
            return 1
        print("pushed; polling status every {0}s".format(POLL_INTERVAL))

        deadline = time.time() + POLL_MAX_SECONDS
        state = "pending"
        while time.time() < deadline:
            try:
                state = worker.kernels_status(ref)
            except Exception as e:
                print(f"  status query failed ({e}); retrying")
                state = "unknown"
            print(f"  [{time.strftime('%H:%M:%S')}] {state}", flush=True)
            if state in ("complete", "error", "failed", "cancelled"):
                break
            time.sleep(POLL_INTERVAL)
        else:
            print("polling deadline reached")
            return 1

        if state != "complete":
            print(f"kernel ended in state '{state}'")
            print("---- last 60 log lines ----")
            print(worker.kernels_logs_tail(ref, 60))
            return 1
        (LOG_DIR / "kernel_console.txt").write_text(
            worker.kernels_logs_tail(ref, 400), encoding="utf-8")
    else:
        print("skipping push (--skip-push); downloading existing output")

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    try:
        worker.kernels_output(ref, OUTPUT_DIR)
    except Exception as e:
        print(f"output download FAILED: {type(e).__name__}: {e}")
        return 1

    return _normalise_output(OUTPUT_DIR)


def _normalise_output(out: Path) -> int:
    """Move results_cpu/ -> results_cpu_kaggle/, keep diagnostics staged."""
    produced = out / "results_cpu"
    if not produced.is_dir():
        print("FATAL: kernel produced no results_cpu/ directory")
        print("contents: " + ", ".join(sorted(p.name for p in out.iterdir()))
              if out.is_dir() else "no output dir")
        return 1

    if CPU_DIR.exists():
        shutil.rmtree(CPU_DIR)
    CPU_DIR.mkdir(parents=True)
    for d in sorted(p for p in produced.iterdir() if p.is_dir()):
        shutil.copytree(d, CPU_DIR / d.name)

    for name in ("run_info.json", "kaggle_cpu_logs"):
        src = out / name
        if src.is_dir():
            if LOG_DIR.exists():
                shutil.rmtree(LOG_DIR)
            shutil.copytree(src, LOG_DIR)
        elif src.is_file():
            shutil.copy2(src, CPU_DIR / name)

    print("\ndownloaded output -> %s" % CPU_DIR)
    for p in sorted(CPU_DIR.iterdir()):
        print("  %s" % p.name)

    info = CPU_DIR / "run_info.json"
    if info.is_file():
        ri = json.loads(info.read_text(encoding="utf-8"))
        print("\nrun_info.json")
        print("  status          : %s" % ri.get("status"))
        print("  commit          : %s" % str(ri.get("commit"))[:12])
        print("  python          : %s" % ri.get("python_version"))
        print("  cpu             : %s" % ri.get("cpu_model"))
        print("  pip_mode        : %s" % ri.get("pip_mode"))
        print("  input dir       : %s" % ri.get("input_dir_detected"))
        print("  total runtime   : %ss" % ri.get("total_runtime_sec"))
        ver = ri.get("versions", {})
        print("  torch           : %s" % ver.get("torch"))
        print("  sentence-transf.: %s" % ver.get("sentence_transformers"))
        for exp, r in sorted(ri.get("experiments", {}).items()):
            print("  %-30s %-6s %ss" % (exp, r.get("status"),
                                        r.get("runtime_sec")))
    return 0


def _numeric(obj) -> dict:
    """Same leaves + same environment-field exclusions as compare_cpu_results."""
    return {k: float(v) for k, v in ccr.leaves(obj)
            if isinstance(v, (int, float)) and not isinstance(v, bool)
            and not any(x in k for x in ccr.EXCLUDE)}


def _pattern_hits(pattern: str, paths) -> list:
    rx = re.compile("^" + re.escape(pattern).replace(r"\[\*\]", r"\[\d+\]") + "$")
    return [p for p in paths if rx.match(p)]


def cmd_gate(_args) -> int:
    if not CPU_DIR.is_dir():
        print(f"FATAL: {CPU_DIR} not found; run `run` first")
        return 1

    print("=" * 78)
    print("step 2a: scripts/compare_cpu_results.py (existing tolerance)")
    print("=" * 78)
    rc = subprocess.call([sys.executable, str(ROOT / "scripts" / "compare_cpu_results.py"),
                          "--cpu-dir", str(CPU_DIR),
                          "--ref-dir", str(REF_DIR),
                          "--report", str(REPORT)])

    # ---- full field-by-field diff (nothing hidden, nothing rounded away) ----
    diffs, missing, extra = [], [], []
    fields_compared = 0
    for exp in sorted(EXPERIMENTS):
        ref_m = REF_DIR / exp / "metrics.json"
        new_m = CPU_DIR / exp / "metrics.json"
        if not new_m.is_file():
            missing.append((exp, "no metrics.json in the Kaggle run"))
            continue
        if not ref_m.is_file():
            missing.append((exp, "no committed metrics.json"))
            continue
        a = dict(_numeric(json.loads(ref_m.read_text(encoding="utf-8"))))
        b = dict(_numeric(json.loads(new_m.read_text(encoding="utf-8"))))
        fields_compared += len(set(a) & set(b))
        for k in sorted(set(a) & set(b)):
            if a[k] != b[k]:
                diffs.append((exp, k, a[k], b[k], abs(a[k] - b[k])))
        for k in sorted(set(a) - set(b)):
            missing.append((f"{exp}:{k}", "in committed, absent in the Kaggle run"))
        for k in sorted(set(b) - set(a)):
            extra.append((f"{exp}:{k}", "in the Kaggle run, absent in committed"))

    print("\n" + "=" * 78)
    print("step 2b: EVERY field that differs (value and absolute difference)")
    print("=" * 78)
    if diffs:
        print(f"  {len(diffs)} field(s) differ:\n")
        print("  %-30s %-44s %14s %14s %14s"
              % ("experiment", "field", "committed", "kaggle", "abs diff"))
        print("  " + "-" * 120)
        for exp, k, va, vb, d in diffs:
            print("  %-30s %-44s %14.6g %14.6g %14.6e"
                  % (exp, k[:44], va, vb, d))
    else:
        print("  none: every numeric field is bit-identical to the committed value")
    if missing:
        print(f"\n  MISSING fields ({len(missing)}):")
        for e, why in missing:
            print("    %s: %s" % (e, why))
    if extra:
        print(f"\n  EXTRA fields not present in the committed artifacts ({len(extra)}):")
        for e, why in extra:
            print("    %s: %s" % (e, why))

    # ---- headline gate at reported precision ----
    print("\n" + "=" * 78)
    print("step 2c: headline gate at reported precision")
    print("=" * 78)
    headline_rows, headline_fail = [], []
    for exp in sorted(HEADLINE):
        ref_m, new_m = REF_DIR / exp / "metrics.json", CPU_DIR / exp / "metrics.json"
        if not (ref_m.is_file() and new_m.is_file()):
            headline_fail.append((exp, "*", "metrics.json missing", "", ""))
            continue
        a = dict(_numeric(json.loads(ref_m.read_text(encoding="utf-8"))))
        b = dict(_numeric(json.loads(new_m.read_text(encoding="utf-8"))))
        for pattern, dp in HEADLINE[exp]:
            keys = _pattern_hits(pattern, sorted(set(a) & set(b)))
            if not keys:
                headline_fail.append((exp, pattern, "no matching field", "", ""))
                continue
            for k in keys:
                va, vb = a[k], b[k]
                ok = round(va, dp) == round(vb, dp)
                headline_rows.append((exp, k, dp, va, vb, ok))
                if not ok:
                    headline_fail.append((exp, k, "precision mismatch",
                                          f"{va!r}", f"{vb!r}"))
    print("  %-30s %-42s %3s %14s %14s %s"
          % ("experiment", "field", "dp", "committed", "kaggle", "ok"))
    print("  " + "-" * 120)
    for exp, k, dp, va, vb, ok in headline_rows:
        print("  %-30s %-42s %3d %14.6g %14.6g %s"
              % (exp, k[:42], dp, va, vb, "yes" if ok else "**NO**"))
    print("  headline fields checked: %d" % len(headline_rows))
    print("  headline mismatches    : %d" % len(headline_fail))
    if headline_fail:
        for row in headline_fail:
            print("    %s" % (row,))

    gate_ok = (rc == 0 and not diffs and not missing and not extra
               and not headline_fail)
    payload = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cpu_dir": str(CPU_DIR.relative_to(ROOT)),
        "comparator_exit_code": rc,
        "fields_compared": fields_compared,
        "fields_differing": len(diffs),
        "fields_missing": len(missing),
        "fields_extra": len(extra),
        "headline_checked": len(headline_rows),
        "headline_mismatches": len(headline_fail),
        "differences": [{"experiment": e, "field": k, "committed": va,
                         "kaggle": vb, "abs_diff": d} for e, k, va, vb, d in diffs],
        "headline_failures": [{"experiment": e, "field": k, "why": w,
                               "committed": c, "kaggle": n}
                              for e, k, w, c, n in headline_fail],
        "gate_passed": bool(gate_ok),
    }
    GATE_JSON.parent.mkdir(exist_ok=True)
    GATE_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("\nwrote %s" % GATE_JSON)
    print(wrote_report_note(REPORT))

    print("\n" + "=" * 78)
    print("GATE: %s" % ("PASS" if gate_ok else "FAIL"))
    print("=" * 78)
    if not gate_ok:
        print("No upload will be attempted. See reports/CPU_VS_COMMITTED_KAGGLE.md")
    return 0 if gate_ok else 1


def wrote_report_note(path: Path) -> str:
    return "wrote %s" % path if path.is_file() else \
        "(no comparison report written)"


# ---------------------------------------------------------------------------
# Hugging Face upload, strict allowlist
# ---------------------------------------------------------------------------
FORBIDDEN_NAME = re.compile(r"(?i)(_key|\.env|sealed|worker_map\.json)")
SECRET_IN_CONTENT = re.compile(
    r"(?i)(hf_[a-z0-9]{25,}|kaggle[_-]?api[_-]?key\s*[:=]|"
    r"Kaggel_Token\s*[:=]|KAGGLE_KEY\s*[:=])")


def _refuse(path: Path) -> str | None:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    if FORBIDDEN_NAME.search(rel):
        return f"path matches a forbidden pattern ({rel})"
    try:
        head = path.read_bytes()[:1_000_000]
    except Exception as e:
        return f"unreadable ({e})"
    if SECRET_IN_CONTENT.search(head.decode("latin-1")):
        return "file content looks like it contains a credential"
    return None


def cmd_upload(_args) -> int:
    gate = json.loads(GATE_JSON.read_text(encoding="utf-8")) if GATE_JSON.is_file() else None
    if not gate or not gate.get("gate_passed"):
        print("REFUSING: the gate has not passed (reports/cpu_kaggle_gate.json "
              "is absent or gate_passed=false).")
        return 1

    token = os.environ.get("HF_TOKEN") or os.environ.get("HF_TOKEN_HF")
    if not token:
        try:
            from dotenv import dotenv_values
            token = dotenv_values(ENV_PATH).get("HF")
        except Exception:
            token = None
    if not token:
        print("REFUSING: no HF token in $HF_TOKEN or the .env key 'HF'.")
        return 1

    from huggingface_hub import HfApi
    api = HfApi(token=token)
    user = api.whoami()["name"]
    repo_id = f"{user}/skill-gap-cpu-verification"
    print(f"target: {repo_id} (dataset)")

    # ---- explicit allowlist ----
    allow: list[Path] = []
    if CPU_DIR.is_dir():
        allow += sorted(p for p in CPU_DIR.rglob("*") if p.is_file())
    if REPORT.is_file():
        allow.append(REPORT)
    if GATE_JSON.is_file():
        allow.append(GATE_JSON)

    refused, clean = [], []
    for p in allow:
        why = _refuse(p)
        (refused if why else clean).append((p, why) if why else p)
    if refused:
        print("REFUSING: candidate files failed the allowlist check:")
        for p, why in refused:
            print(f"  {p.relative_to(ROOT)}: {why}")
        return 1

    print("allowlist (%d files):" % len(clean))
    for p in clean:
        print("  %s" % p.relative_to(ROOT))

    api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
    for p in clean:
        arc = str(p.relative_to(ROOT)).replace("\\", "/")
        print(f"  uploading {arc}")
        api.upload_file(path_or_fileobj=str(p), path_in_repo=arc,
                        repo_id=repo_id, repo_type="dataset")
    url = f"https://huggingface.co/datasets/{repo_id}"
    print(f"\nuploaded -> {url}")
    return 0


def cmd_all(args) -> int:
    for fn in (cmd_build, cmd_run, cmd_gate):
        rc = fn(args)
        if rc:
            return rc
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", choices=["build", "run", "gate", "upload", "all"])
    ap.add_argument("--skip-push", action="store_true",
                    help="with `run`: download an already-pushed kernel's output")
    ap.add_argument("--commit", default=None,
                    help="commit the kernel should clone (default: the commit "
                         "origin/main currently serves)")
    args = ap.parse_args()
    return {"build": cmd_build, "run": cmd_run, "gate": cmd_gate,
            "upload": cmd_upload, "all": cmd_all}[args.phase](args)


if __name__ == "__main__":
    raise SystemExit(main())
