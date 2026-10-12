# Academic–Industry Skill-Gap Study — reviewer bundle

Double-blind review bundle. Author identities, institution, and all account
handles have been removed; the version history is not included (this directory
is a flat export of one commit).

## What is here

| Path | Contents |
| --- | --- |
| `paper/` | main manuscript (`main.tex`, `main.pdf`), tables, figures, bibliography |
| `paper_placement/` | companion benchmark-audit article (separate submission) |
| `datasets/` | dataset manifest, checksums, provenance audit (`REAL_VS_SYNTHETIC.csv`), executable generator-signature checks and their outputs, the eight-category skill taxonomy, the curriculum-selection protocol and extracted phrase set |
| `experiments/` | the registered experiment scripts and the LaTeX/table generator |
| `results/` | per-experiment `metrics.json` and derived tables (no run metadata, no registry, no worker map) |
| `tests/` | the test suite that re-derives the published numbers |
| `reproduce_local.py` | one-command reproduction driver |
| `requirements.txt` | pinned dependencies |

Deliberately **not** included: the audit trail and revision reports, archived
experiment reports, the blinded labelling files, run/registry metadata that
carries host account names, the CC-licensed CS2023 Body of Knowledge PDF (the
derived topic list is included instead), and the raw datasets themselves.

## Reproducing the numbers

Raw inputs are not redistributed here. They are listed, with licence and
checksum, in `datasets/DATASET_MANIFEST.csv` and `datasets/input_checksums.sha256`;
fetch them from their stated public sources, then:

```bash
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python -m pytest                         # unit tests (the two that need raw
                                         # inputs or the withheld audit trail
                                         # skip themselves)
python experiments/verify.py             # sanity checks over results/
```

The manuscript-claim verification layer (`audit/verify_claims.py`, which
re-derives all 103 checked claims from the artifacts, plus the claim–evidence
ledger) is withheld from the blinded bundle because it is part of the internal
audit trail; it is available to the editors on request.

Every experiment fixes its random seed (42), pins its embedding model, and is
CPU re-runnable; no result depends on GPU hardware or on a hosted notebook.
