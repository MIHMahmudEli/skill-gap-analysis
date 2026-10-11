# Phase 8 — Reproducibility Infrastructure

*Date: 2026-10-11 · Branch: `q1-readiness-audit`*

## 8.1 Gaps Found in Phase 0 Inventory (now closed)

| Gap | Status |
|---|---|
| No automated tests | **Closed**: `tests/test_common.py` (8 unit tests), `tests/test_reproducibility.py` (6 integration/smoke tests) |
| No CI | **Closed**: `.github/workflows/ci.yml` (pytest + claim ledger + citation check) |
| No input integrity hashes | **Closed**: `datasets/compute_checksums.py` → `datasets/input_checksums.sha256` (9/9 bundle files, SHA-256) |
| No single entry point | **Closed**: `reproduce_local.py` (env pin → checksums → verify.py → claim ledger → stats → citations) |
| Manifest record-count errors (D-2/D-3) | **Fixed in this phase** (see 8.2) |

## 8.2 Manifest Corrections Applied

`datasets/DATASET_MANIFEST.csv` — actual file counts (pandas-verified) replace
incorrect values; correction notes added in `domain_and_notes`:

| Dataset | Was | Now | Evidence |
|---|---|---|---|
| LinkedIn Jobs & Skills | 1,348,510 | **1,348,454** | local `linkedin_job_postings.csv` rows |
| HF Skill Gap Jobs | 519,841 | **519,814** | local `hf_skill_gap_jobs.csv` rows; job_link set ≡ skills table |
| HF Job Skill Set | 13,833 | **1,167** | local `hf_job_skill_set.csv` rows; 5 occupational categories |

No raw data or experiment outputs were modified.

## 8.3 Test Suite Design

- **Unit** (`tests/test_common.py`): `utc_now` format, `sha256_file` known
  vector, JSON round-trip, `experiment_metadata` shape, bundle/local-fallback
  key parity, multi-worker `.env` parsing, missing-input `FileNotFoundError`.
- **Integration** (`tests/test_reproducibility.py`):
  - registry = 12 × `USED_IN_MANUSCRIPT`;
  - every registry `metrics.json` exists and `status=completed`;
  - `verify.py` REQUIRED map ⊆ `results/` directories;
  - manifest counts == local CSV rows (skips if raw CSVs absent);
  - `verify_claims.py` exit 0 + ledger ≥ 90 rows (structural; contradiction
    count becomes a hard gate **after** Phase 9 manuscript fixes);
  - `input_checksums.sha256` well-formed (64-hex digests).
- All tests skip data-dependent cases when gitignored inputs are missing →
  green in a fresh clone.

**Local run (2026-10-11):** `13 passed` after fixing two test harness bugs
(KeyError vs FileNotFoundError; quoted-CSV line counting → pandas row count).

## 8.4 Single Entry Point: `reproduce_local.py`

```
python reproduce_local.py              # all stages
python reproduce_local.py --skip citations
python reproduce_local.py --only stats
```

| Stage | Script | Needs |
|---|---|---|
| env | inline pin check vs `requirements.txt` | installed packages |
| checksums | `datasets/compute_checksums.py` | local raw CSVs |
| verify | `experiments/verify.py` | `results/` |
| claims | `audit/verify_claims.py` | `results/` |
| stats | `audit/reproduce_stats.py` | local college/ intl CSVs |
| citations | `audit/verify_citations.py` | network (Crossref) |

Kaggle GPU re-runs remain documented in `README.md` (require credentials;
not part of the local entry point).

## 8.5 CI Workflow

`.github/workflows/ci.yml` — Python 3.12, `requirements.txt` + pytest,
runs unit/integration tests, claim-ledger reproduction, and a
`continue-on-error` Crossref citation check (network flakiness must not
block merges). Triggered on `main` and `q1-readiness-audit`.

## 8.6 Residual Known Limits

- Large raw CSVs stay gitignored; checksums are the integrity anchor.
- `verify_claims.py` currently still reports the H6/D-1 contradiction —
  expected until Phase 9 manuscript fixes land; the test only gates
  script success + ledger structure for now.
- Line-by-line audit of CS2023 2,197-topic extraction remains out of scope
  (Phase 0 risk R5), unchanged.
