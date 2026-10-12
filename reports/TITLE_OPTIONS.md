# Title options — batch 4, step 2

Author instruction 2026-10-12: choose a **measurement-audit title conditioned on
findings**, apply option 1, print three options, and keep the candidate
strong-branch title here for a later swap.

## Applied (option 1)

> **Lexical versus Semantic Skill-Gap Measurement: A Sensitivity Audit on Job-Posting Data**

Set in `paper/main.tex` line 44. The companion article's `\thanks`
cross-reference in `paper_placement/main.tex` was updated to match, so the two
papers still name each other correctly.

### Why this title fits the findings

- **"Lexical versus Semantic"** — the paper's central empirical result *is* the
  contrast between the two instruments: SGI 52% (exact string) vs 32%
  (Sentence-BERT, τ = 0.5), a 20 pp spread. The title states the axis the
  results are organised along.
- **"Measurement"** — deliberately not "skills gap", "misalignment", or
  "divide". The contribution is that the *measured* gap is instrument-dependent,
  which is a measurement claim, not a claim that a gap of a given size exists.
- **"Sensitivity Audit"** — matches what the paper actually runs: a τ sweep
  across four thresholds, a (K, P) grid swept by SENS01 (lexical
  [0.52, 0.73], semantic-at-τ0.5 [0.26, 0.42]), a nested-superset re-check on
  1.29M postings, multi-seed robustness, and an external matcher validation
  (κ = 0.737). "Audit" also signals the negative/limiting results are in scope.
- **"Job-Posting Data"** — names the evidence base without naming a vendor, a
  scrape, or a platform, and without claiming curricular data (the paper
  explicitly does *not* have institutionally collected syllabi).

## Options considered

| # | Title | Verdict |
|---|---|---|
| **1** | **Lexical versus Semantic Skill-Gap Measurement: A Sensitivity Audit on Job-Posting Data** | **Applied.** Names the central contrast, scopes the claim to measurement, and commits to the audit framing that the results support. |
| 2 | How Much of the Academic–Industry Skill Gap Is Vocabulary? A Multi-Threshold and Multi-Corpus Sensitivity Analysis | Strong, and it front-loads the paper's most quotable finding (the 20 pp lexical→semantic reduction *is* consistent with vocabulary divergence). Rejected because it states the causal reading as the headline, whereas the manuscript only says the reduction is *consistent with* vocabulary divergence accounting for *part* of the gap — a causal-sounding title outruns the evidence. |
| 3 | The Skill Gap Index Is Instrument-Dependent: A Reproducibility and Sensitivity Study over Job Postings | Accurate and honest, and "reproducibility" is defensible given the CPU re-run and the artifact-verification story. Rejected as the primary because it leads with a limitation rather than with the measurement contrast, and because full reproducibility is *not* claimed (5 embedding experiments are unverified on CPU), so the word invites a reviewer question the paper then has to partly answer in the negative. |

## Candidate strong-branch title — saved for a later swap

This is the title intended for the paper once the strong-branch (fully supported,
non-limiting) framing is wanted. **Not applied now**; swap it in when the author
rules.

```
Lexical versus Semantic Skill-Gap Measurement: A Sensitivity Audit on Job-Posting Data
```

If the strong branch should instead foreground the substantive finding rather
than the audit, the reserved alternative is:

```
A 20-Point Instrument Effect in Academic–Industry Skill-Gap Measurement
```

To swap: edit `\title{}` in `paper/main.tex`, update the `\thanks`
cross-reference in `paper_placement/main.tex`, rebuild both PDFs, and rerun the
gates. No other file pins either string — checked: `audit/01_claim_evidence_ledger.{csv,md}`
contains no title reference, and README's only `title=` is the BibTeX entry for
the software itself, which is unchanged.

## Note — the old title is retained in one historical file

`reports/ABSTRACT_V2_DRAFT.md` line 88 quotes the superseded title. That is a
dated historical draft and is deliberately left unedited so the revision trail
stays auditable.
