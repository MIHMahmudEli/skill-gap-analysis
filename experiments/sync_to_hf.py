"""Upload verified experiment results to the Hugging Face archive.

Creates/updates the dataset repo <hf_user>/skill-gap-experiments with:
  - registry.json, verification_report.json
  - one folder per experiment: metrics.json + CSV/JSON artifacts + metadata.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ENV_PATH, REGISTRY_PATH, RESULTS_DIR, REPO_ROOT,
                    experiment_metadata, git_commit, read_json, utc_now,
                    write_json)

HF_REPO = None  # resolved at runtime


def main() -> None:
    from dotenv import dotenv_values
    from huggingface_hub import HfApi

    vals = dotenv_values(ENV_PATH)
    token = vals.get("HF")
    api = HfApi(token=token)
    user = api.whoami()["name"]
    repo_id = f"{user}/skill-gap-experiments"

    reg = read_json(REGISTRY_PATH)
    verified = [eid for eid, e in reg["experiments"].items()
                if e["status"] == "VERIFIED"]
    print(f"HF user: {user}; verified experiments: {verified}")

    api.create_repo(repo_id, repo_type="dataset", exist_ok=True,
                    private=False)

    # top-level files
    api.upload_file(
        path_or_fileobj=str(REGISTRY_PATH),
        path_in_repo="registry.json",
        repo_id=repo_id, repo_type="dataset",
    )
    vr = RESULTS_DIR / "verification_report.json"
    if vr.exists():
        api.upload_file(path_or_fileobj=str(vr),
                        path_in_repo="verification_report.json",
                        repo_id=repo_id, repo_type="dataset")

    dataset_keys = {
        "ALIGN01_lexical_bootstrap": ["market_skills", "academic_skills"],
        "ALIGN02_semantic_sbert": ["market_skills", "academic_skills"],
        "ALIGN03_domain_gap": ["market_skills", "academic_skills"],
        "STAT01_placement_core": ["college_placement"],
        "STAT02_external_validation": ["college_placement", "student_career",
                                       "global_placement"],
        "GEO01_linkedin_shares": ["linkedin_postings"],
        "TRENDS01_ai_longitudinal": ["ai_trends"],
        "INTL01_internship_effect": ["international_grads"],
        "PLAC01_global_by_country": ["global_placement"],
        "VALID01_esco_gold": ["market_skills", "academic_skills"],
    }

    for exp_id in verified:
        d = RESULTS_DIR / exp_id
        if not d.exists():
            print(f"skip {exp_id}: no directory")
            continue
        files = sorted(p for p in d.rglob("*")
                       if p.is_file() and p.name != "kernels_logs_tail.txt")
        if not files:
            continue
        meta = experiment_metadata(
            exp_id,
            dataset_keys.get(exp_id, []),
            model=reg["experiments"][exp_id].get("model", "see metrics.json"),
            hyperparameters=json.loads(json.dumps(
                reg["experiments"][exp_id].get("hyperparameters", {}))),
            protocol=reg["experiments"][exp_id].get("protocol",
                                                    "see metrics.json"),
        )
        meta["kaggle_kernel_ref"] = reg["experiments"][exp_id].get("kernel_ref")
        meta["worker"] = reg["experiments"][exp_id].get("worker")
        metrics_path = d / "metrics.json"
        if metrics_path.exists():
            m = json.loads(metrics_path.read_text(encoding="utf-8"))
            meta["runtime_sec"] = m.get("runtime_sec")
            meta["seed"] = m.get("seed", meta["seed"])
        write_json(d / "metadata.json", meta)
        api.upload_folder(
            folder_path=str(d),
            path_in_repo=f"experiments/{exp_id}",
            repo_id=repo_id, repo_type="dataset",
        )
        print(f"uploaded {exp_id} ({len(files)} files)")

    print(f"\nArchive: https://huggingface.co/datasets/{repo_id}")


if __name__ == "__main__":
    main()
