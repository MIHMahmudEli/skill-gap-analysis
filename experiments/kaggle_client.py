"""Thin wrapper around the Kaggle CLI, parameterised by worker token."""
from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path


class KaggleWorker:
    def __init__(self, username: str, token: str, index: int):
        self.username = username
        self.token = token
        self.index = index

    def _env(self):
        env = os.environ.copy()
        env["KAGGLE_API_TOKEN"] = self.token
        # Kaggle CLI progress/logs may emit unicode; force UTF-8 to avoid
        # Windows cp1252 charmap crashes in the subprocess.
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        return env

    def _run(self, args, timeout=1200):
        proc = subprocess.run(
            ["kaggle", *args],
            capture_output=True, text=True, timeout=timeout, env=self._env(),
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"kaggle {' '.join(args)} failed ({proc.returncode}): "
                f"{proc.stderr[:800]} {proc.stdout[:400]}"
            )
        return proc.stdout

    def kernels_push(self, folder: Path, accelerator: str | None = "GPU",
                     timeout: int = 7200):
        # accelerator=None omits --accelerator entirely, which leaves the
        # metadata's enable_gpu flag in force (CPU-only runs set it false).
        args = ["kernels", "push", "-p", str(folder)]
        if accelerator:
            args += ["--accelerator", accelerator]
        args += ["-t", str(timeout)]
        return self._run(args)

    def kernels_status(self, ref: str) -> str:
        out = self._run(["kernels", "status", ref]).strip().lower()
        # CLI v2 emits e.g. 'KernelWorkerStatus.ERROR' / '.QUEUED'.
        m = re.search(r"kernelworkerstatus\.(\w+)", out)
        if m:
            state = m.group(1).lower()
            return {"complete": "complete", "completed": "complete",
                    "error": "error", "failed": "failed",
                    "cancelled": "cancelled", "canceled": "cancelled",
                    "running": "running", "queued": "pending",
                    "saving": "saving", "pending": "pending"}.get(state, state)
        for state in ("complete", "failed", "cancelled", "error", "running",
                      "saving", "pending"):
            if state in out:
                return state
        return out or "unknown"

    def kernels_output(self, ref: str, dest: Path):
        dest.mkdir(parents=True, exist_ok=True)
        self._run(["kernels", "output", ref, "-p", str(dest), "-o", "-q"], timeout=1800)

    def kernels_logs_tail(self, ref: str, lines: int = 40) -> str:
        try:
            proc = subprocess.run(
                ["kaggle", "kernels", "logs", ref, "-p", "0"],
                capture_output=True, text=True, timeout=120, env=self._env(),
            )
            return "\n".join(proc.stdout.splitlines()[-lines:])
        except Exception as e:
            return f"<logs unavailable: {e}>"

    def dataset_create(self, folder: Path):
        return self._run(["datasets", "create", "-p", str(folder)], timeout=7200)

    def dataset_status(self):
        return self._run(["datasets", "list", "-m", "-s", "skill-gap-inputs"], timeout=300)


def build_kernel_folder(
    kernel_dir: Path,
    worker: KaggleWorker,
    slug: str,
    script_path: Path,
    dataset_sources: list[str],
    enable_gpu: bool = True,
    enable_internet: bool = False,
) -> Path:
    kernel_dir.mkdir(parents=True, exist_ok=True)
    dest_script = kernel_dir / "exp_script.py"
    dest_script.write_text(script_path.read_text(encoding="utf-8"), encoding="utf-8")
    # Kaggle derives the live kernel slug from the TITLE (slugified), not the
    # metadata id, so title must slugify to exactly `slug`.
    meta = {
        "id": f"{worker.username}/{slug}",
        "title": slug,
        "code_file": "exp_script.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": enable_gpu,
        "enable_internet": enable_internet,
        "dataset_sources": dataset_sources,
        "competition_sources": [],
        "kernel_sources": [],
        "save_output": True,
    }
    import json
    (kernel_dir / "kernel-metadata.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8")
    return kernel_dir
