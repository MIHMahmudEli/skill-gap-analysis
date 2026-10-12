# Identity audit — where the author's name and email appear

Author instruction 2026-10-12 (batch 4, step 3). **Print-only audit** plus one
config change. **No history was rewritten** — no `filter-branch`, no rebase, no
force-push. Every one of the 72 commits across all refs still carries the real
identity, and that is intentional: rewriting public history to hide an identity
is both impossible in practice (the pushed commits are cached and forked) and
destructive to the record.

## 1. Commit metadata

A single identity, on **every** commit, author and committer, all refs:

```
MIHMahmudEli <mdmohsin11222@gmail.com>
```

72 commits total, all matching. Note the spelling: **`mdmohsin11222`** (m-o-h-**s**-i-n),
which is easy to mistype as `mdmohdin…`; the reviewer-bundle identifier list has it
correct.

## 2. Tracked files containing identity strings

Real hits, grouped by whether they are *functional* (the code needs the literal
string to run) or *cosmetic* (safe to neutralize).

### Functional — required for the pipeline to run

| File:line | String | Why it must stay |
|---|---|---|
| `experiments/common.py:29` | `studyhub991/skill-gap-inputs-v1` | Kaggle dataset id used to stage inputs |
| `experiments/stage_inputs.py:20,35,36` | `studyhub991` | resolves the Kaggle worker username |
| `experiments/exp_scripts/*.py` (13 files) | `/kaggle/input/datasets/studyhub991/…` | the Kaggle mount path each experiment's `resolve()` tries |
| `results/registry.json:616`, `results/worker_map.json:63-64` | `studyhub991` | recorded provenance of the runs that produced the artifacts |

These are not anonymizable by editing: the path is where the data actually lives on
the execution host. The **reviewer bundle** already handles this by string-replacing
them at build time (`scripts/make_reviewer_bundle.sh` → `<INPUT_BUNDLE>`,
`<ACCOUNT>`), which is the right pattern.

### Cosmetic — safe to neutralize, pending your ruling

| File:line | String |
|---|---|
| `LICENSE:3` | `Copyright (c) 2026 MIHMahmudEli` |
| `README.md:147,188,189,225` | Kaggle bundle URL, HF archive URL, GitHub repo URL in the BibTeX |
| `audit/00_repository_inventory.md:57-58`, `audit/12_final_readiness_report.md:100` | bundle + HF archive names |
| `archive/EXPERIMENT_REPORT.md:11,15,18,119`, `archive/Q1_READINESS.md:22` | HF + Kaggle names |
| `experiments/make_latex.py:9` | HF archive name in a docstring |
| `reports/CLEAN_ROOM_REPRO.md:88` | `kaggle datasets download -d studyhub991/…` in a copy-pasteable command |

### Self-referential — these *are* the guard, not a leak

`scripts/verify_reviewer_bundle.sh:17-18` and `reports/Q1_REVISION_PLAN.md:222` list
the identifiers **in order to detect and remove them**. `scripts/make_reviewer_bundle.sh`
and `archive/align05_titles_200_key_RETIRED.md` / `experiments/ALIGN05_PREREG.md`
(`MIHMahmudEli/skill-gap-analysis`) name the repo only to explain the leak. Do not
"clean" the verifier's list — it is the detector.

### Clean

- **Both PDFs** (`paper/main.pdf`, `paper_placement/main.pdf`) contain none of the
  identifier list.
- **Both `.tex` author blocks** read `Author Names Redacted for Double-Blind Peer Review`.
- No tracked file contains the email address itself.

## 3. What I changed

Repo-local config only, so **future** commits are no-reply; the global config and
all history are untouched:

```
git config user.name  "MIHMahmudEli"
git config user.email "MIHMahmudEli@users.noreply.github.com"
```

`git var GIT_AUTHOR_IDENT` now reports the no-reply form for the next commit.
`git log --all` still reports the real identity on all 72 existing commits.

## 4. GitHub-side settings you should change yourself

I cannot reach these — no `gh` CLI is installed and I hold no credentials. They
are yours to set:

1. **Make the repository private** (Settings → Danger Zone → Change visibility).
   This is the single highest-value action: it removes the published ALIGN05 key,
   the identity strings and the whole history from public view at a stroke.
   Note it does **not** unpublish already-forked copies or GitHub's CDN cache.
2. **Set a noreply reply address** (Settings → Emails): keep *"+/-  Keep my
   email addresses private"* enabled, and note the assigned
   `ID+MIHMahmudEli@users.noreply.github.com` form. I used the short form
   (`MIHMahmudEli@users.noreply.github.com`) because the numeric-ID form needs
   your account ID, which I cannot look up; both hide the real address, but only
   the ID form is guaranteed to attribute commits to your account. If you want
   the ID form, replace the repo-local `user.email` with it.
3. **Revoke any leaked tokens**: the repo references Kaggle and HuggingFace
   accounts by name. If any token was ever committed or embedded in a workflow,
   rotate it (Kaggle → Settings → API; HF → Settings → Access Tokens). I found no
   token in the tree, but rotation is cheap insurance.
4. **Delete stale branches you do not need** (`q1-readiness-audit`,
   `q1-readiness-package`) — they carry the same identity metadata and widen the
   surface without adding value.
5. **Consider `git scrub` semantics only via a new repo**: if you want a genuinely
   clean public history, the honest route is a fresh repository containing a
   single squashed import, not a rewrite of this one. That is a decision for you,
   and it invalidates all existing commit references in the trackers.

## 5. What I deliberately did not do

- Did **not** rewrite history to scrub the identity from the 72 commits.
- Did **not** edit the functional `studyhub991` strings in the experiment scripts,
  registry or worker map — doing so would break reproducibility of the committed
  artifacts, and the reviewer-bundle sanitizer already covers the submission path.
- Did **not** touch `LICENSE`, `README` or the archive files: those are cosmetic
  identity strings, and changing them is your call, not a silent sweep.
