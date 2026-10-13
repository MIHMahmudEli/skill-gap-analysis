# COHERENCE_AUDIT — paper/main.tex against the measurement-audit title

**Status: ANALYSIS ONLY. Nothing in `paper/main.tex` was changed by this pass.**
**Baseline for "what changed": commit `9ca13e2` (and `0aa1ac2`, the last push).**

Title under audit:

> **Lexical versus Semantic Skill-Gap Measurement: A Sensitivity Audit on Job-Posting Data**

That title declares three things: the object is *measurement*, the method is a
*sensitivity audit*, and the data are *job postings*. Any sentence that instead
presents the paper as (a) establishing that curricula fall short, (b) treating a
posting-derived profile as if it were curricula, (c) doing HCT/Constructive
Alignment work, or (d) closing a workforce divide, is out of scope for the title
and reads as a different paper.

---

## Counts

| Category | Sentences flagged |
|---|---|
| **(a)** claims or implies a curricular gap | **17** |
| **(b)** calls the reference profile "academic"/"curriculum" without the reference-profile qualifier | **9** |
| **(c)** relies on HCT / Constructive Alignment framing the measurement-audit scope no longer uses | **12** |
| **(d)** frames the paper as bridging a workforce divide | **16** |
| **Total distinct sentences** | **40** (many carry two or three tags; tags total 54) |

Plus **one recommended new sentence** (T1) for §5.6 Threats, where no current
sentence violates a category but the section is missing the disclaimer the
title now implies — so 40 flagged + 1 proposed = 41 items below.

Scanning method: every sentence in `paper/main.tex` was matched against trigger
patterns for all four categories (127 raw candidates), then read in context and
curated. False positives discarded: `Skill Gap Index`/`SGI` used as an instrument
name, `\texttt{skill-gap-analytics/...}` dataset identifiers, table and registry
rows, and every occurrence that already carries the qualifier
("academic reference profile", "reference-profile deficit").

---

## The 10 most important items

Ranked by how directly the sentence contradicts the word *audit* in the title.

### 1. Conclusion — "addressing this divide" (L549, cat. d)
> In practical terms, addressing this divide does not necessitate wholesale curriculum redesign.

Presupposes a divide exists and that the paper's purpose is to address it.
Neither is established: the paper measures a posting-derived profile against a
market corpus.

**Proposed:** "If the residual reference-profile deficits correspond to real
curricular shortfalls, addressing them would not necessitate wholesale curriculum
redesign — an inference we mark as conditional and do not test here."

### 2. Conclusion — closing sentence (L549, cat. d)
> Integrating modular credentials into established courses and assessing applied skills inside core courses offer feasible steps toward aligning academic preparation with contemporary workforce demands.

The paper's final sentence is a bridge-building prescription, the exact framing
the title drops.

**Proposed:** "Because the measurements cannot by themselves separate vocabulary
divergence from curricular shortfall, the next step is a study that measures
curricula directly; the modular-credential and assessment options in Section 5
remain candidate responses conditional on such evidence."

### 3. Contribution 5 (L110, cat. c + d)
> **Theory-Informed Recommendations:** Drawing on Human Capital Theory and Constructive Alignment, we outline practical adjustments for course design and for assessment embedded in core courses…

Theory is used as the basis for producing course-design prescriptions — a claim
a measurement audit cannot support.

**Proposed:** "**Theory-Informed Interpretation:** We use Human Capital Theory
and Constructive Alignment to *interpret* the measured lexical-versus-semantic
differences, and we keep those interpretations separate from the measurement
claims, which stand independently of any theory."

### 4. Implications opening (L496, cat. d)
> We organize recommendations for higher education and accreditation around the empirical findings:

States outright that empirical findings generate recommendations.

**Proposed:** "We separate what the measurements support from what would require
evidence beyond this study; the latter are offered as questions for institutions,
not as findings:"

### 5. RQ3 (L99, cat. a)
> **RQ3 (Domain-Specific Deficits):** What is the magnitude of the skill deficit across distinct subject areas…?

Asks for the magnitude of a *deficit* with no object — reads as "how big is the
curricular gap", which the abstract explicitly declines to claim.

**Proposed:** "**RQ3 (Domain-Level Reference-Profile Deficits):** What is the
magnitude of the reference-profile coverage deficit across distinct subject areas
(Programming, Data Science, Cloud Infrastructure, Soft Skills, Cybersecurity)?"

### 6. Hypothesis verdict (L463, cat. a + c)
> H1 (constructive alignment) is supported on the primary corpus…

H1 predicts that *curricular coverage* is incomplete for technical toolchains.
Declaring it "supported" converts a measurement of a posting-derived profile into
confirmation of a curricular claim.

**Proposed:** "H1, a constructive-alignment prediction about curricular coverage,
is *consistent with* the measurements: technical categories carry the only
nonzero reference-profile deficits while soft skills are fully covered. Because
the instrument measures a posting-derived profile rather than curricula, we
report consistency, not confirmation of the curricular claim."

### 7. Abstract opening sentence (L70, cat. a + d)
> Disparities between what computing curricula teach and what employers demand are reported, yet such measurement at scale remains limited.

Opens by asserting the disparity as fact, then pivots to measurement.

**Proposed:** "Comparisons between what computing curricula teach and what
employers require are widely reported, but measuring either side at scale remains
limited; we treat that comparison as a measurement problem." *(+1 word over the
current sentence — must be paid for; the abstract is at 248/250.)*

### 8. Conclusion — "substantive residual gaps remain" (L549, cat. a + b)
> …while substantive residual gaps remain concentrated in rapidly evolving technical areas, specifically Cloud Infrastructure and Programming & Development.

Asserts that real gaps *remain*, which is the one claim the paper says it cannot
make; also "academic descriptors" below it lacks the qualifier.

**Proposed:** "…while substantive residual *reference-profile* deficits remain
concentrated in rapidly evolving technical areas — Cloud Infrastructure and
Programming & Development. Whether those residuals correspond to curricular
shortfalls is not established by this study."

### 9. Keywords (L74, cat. a + c + d)
> Skills gap, Higher education, Employability, Natural Language Processing, Sentence-BERT, Curriculum alignment, Human capital theory, Data provenance.

`Skills gap` (unqualified object), `Curriculum alignment` and `Human capital
theory` (the two theories the audit scope sets aside as framing) and
`Employability` (divide framing) all index the paper as the pre-audit paper.

**Proposed:** `Skill-gap measurement, Job-posting analytics, Employability,
Natural Language Processing, Sentence-BERT, Curriculum alignment, Human capital
theory, Data provenance.` — *note:* if HCT/Constructive Alignment are retained as
interpretive lenses (items R3–R5 below), keeping those two keywords is coherent;
`Skills gap` → `Skill-gap measurement` and `Higher education` → `Job-posting
analytics` are the two changes that actually align the keywords with the title.

### 10. HEI recommendation (L500, cat. d)
> HEIs can address this by embedding modular, vendor-neutral technical modules (e.g., containerization fundamentals, cloud storage basics) directly into existing operating systems and database courses.

"Address this" points back at a curricular gap the study does not establish.

**Proposed:** "If the measured reference-profile deficit corresponds to a real
curricular gap — an inference this study does not test — embedding modular,
vendor-neutral technical modules (e.g., containerization fundamentals, cloud
storage basics) directly into operating systems and database courses would be one
response. We flag this as an implication requiring independent curriculum-level
evidence."

---

## Full list, section by section

Legend: **a** curricular-gap claim · **b** unqualified "academic"/"curriculum" ·
**c** HCT / Constructive Alignment framing · **d** workforce-divide framing.

### Front matter

| # | Line | Cat | Current text (excerpt) | Proposed rewrite (excerpt) |
|---|---|---|---|---|
| F1 | L74 | a c d | `Skills gap, Higher education, Employability, … Curriculum alignment, Human capital theory` | `Skill-gap measurement, Job-posting analytics, Employability, …` |
| F2 | L70 | a d | "Disparities between what computing curricula teach and what employers demand are reported, yet such measurement at scale remains limited." | "Comparisons between what computing curricula teach and what employers require are widely reported, but measuring either side at scale remains limited; we treat that comparison as a measurement problem." |

*Abstract is 248/250 words; F2 costs +2 words and must be paid for elsewhere.*
*Abstract pins from `verify_claims`: `LinkedIn`, `Programming \& Development`,
`a computational anchor, not a human audit`, `category`,
`employer-derived occupational reference profile (1,167 job postings`.*

### §1 Introduction (L80–117)

| # | Line | Cat | Current text (excerpt) | Proposed rewrite (excerpt) |
|---|---|---|---|---|
| I1 | L83 | a | "Because university curricula are updated through multi-year institutional review cycles, degree programs often adapt more slowly than market demands evolve." | "…, curricula and market skill demands plausibly change at different rates — a difference this paper measures rather than presumes." |
| I2 | L83 | a d | "Educational researchers and labor economists refer to this discrepancy as the *skills gap* — the divergence between competencies taught in degree programs and the practical proficiencies sought by employers." | "…label this *perceived* difference the *skills gap* — defined as the divergence between competencies taught in degree programs and the practical proficiencies sought by employers. We treat that divergence as a quantity to be measured, not an established fact." |
| I3 | L85 | a | "…employer surveys regularly report deficits in transferable competencies such as professional communication and collaborative problem-solving." | "…employer surveys frequently report *perceived* shortfalls in transferable competencies such as…" |
| I4 | L87 | d | "Prior empirical research on curriculum--market alignment exhibits four main limitations:" | "Prior empirical work on curriculum-to-market comparison exhibits four main limitations:" |
| I5 | L92 | a c d | "Computational employability models are frequently reported without reference to economic or educational frameworks that explain curriculum lag." | "…without reference to economic or educational frameworks that would explain *why* curricula and market demands might diverge — frameworks used here to interpret measurements, not to presume their outcome." |
| I6 | L99 | a | "**RQ3 (Domain-Specific Deficits):** What is the magnitude of the skill deficit across distinct subject areas…?" | "**RQ3 (Domain-Level Reference-Profile Deficits):** What is the magnitude of the reference-profile coverage deficit across distinct subject areas…?" |
| I7 | L107 | a | "…we show that exact matching yields a 52.0% gap, whereas semantic vector alignment reduces this estimate to 32.0% at τ = 0.5." | "…we show that exact matching yields a lexical SGI of 52.0% — a measurement, not a curricular gap size — whereas semantic vector alignment lowers the estimate to 32.0% at τ = 0.5." |
| I8 | L110 | c d | "**Theory-Informed Recommendations:** Drawing on HCT and Constructive Alignment, we outline practical adjustments for course design and for assessment embedded in core courses…" | "**Theory-Informed Interpretation:** We use HCT and Constructive Alignment to *interpret* the measured lexical-versus-semantic differences, keeping those interpretations separate from the measurement claims." |
| I9 | L113 | d | "…discusses theoretical and institutional implications, practical recommendations, reproducibility, and threats to validity." | "…discusses theoretical implications, an institutional reading of the measurements, reproducibility, and threats to validity." |

*RQ1 (L97) and RQ2 (L98) conform — RQ2 already says "academic reference-profile
descriptors". Contribution 1 (L106) and contribution 3 (L108) conform.*

### §2 Related Work and Theoretical Foundations (L118–152)

| # | Line | Cat | Current text (excerpt) | Proposed rewrite (excerpt) |
|---|---|---|---|---|
| R1 | L121 | a | `\subsection{Conceptualizations of the Skills Gap}` | `\subsection{Conceptualizations of the Skills Gap (Literature)}` — *optional; it is a review of others' usage, so low priority* |
| R2 | L123 | a | "The skills gap encompasses macroeconomic, institutional, and pedagogical dimensions." | "The term *skills gap* is used across macroeconomic, institutional and pedagogical traditions with no settled operational definition — an ambiguity that motivates measuring it explicitly." |
| R3 | L132 | a c | "Universities prioritize general human capital because their mission centers on enduring principles." | "Universities are commonly characterised as prioritizing general human capital because their missions center on enduring principles; we use this as an interpretive lens, not as a premise of the measurement." |
| R4 | L134 | a c | "At an institutional level, curriculum lag can be understood as *external misalignment*:" | "At an institutional level, any measured divergence can be read through constructive alignment as *external misalignment* —" |
| R5 | L134 | c | "ILOs are governed by multi-year accreditation reviews (such as ABET and ACM/IEEE guidelines), whereas industry skill demands evolve on shorter market cycles." | append: "We report this as one interpretation of the measurements, not as a premise of the instrument." |
| R6 | L136 | b | `\subsection{Natural Language Processing for Curriculum Analytics}` | `\subsection{Natural Language Processing for Skill-Gap Measurement}` |
| R7 | L138 | b | "…to quantify alignment between market requirements and **academic descriptors** across multiple similarity thresholds…" | "…alignment between market requirements and **reference-profile descriptors**…" |

*L132 HCT definition block is literature and conforms. L132 final sentence —
"This distinction helps explain why measured reference-profile deficits
concentrate in applied toolchains" — is the **model sentence** for how theory
should be used here: it names the deficits as *measured reference-profile*
deficits.*

### §3 Methodology (L153–285)

Methodology is the cleanest section: the proxy is disclosed at L218 ("Academic
skill requirements are represented using a standardized occupational--educational
reference profile … rather than scraped syllabi — a proxy whose content validity
is quantified against CS2023 in CURR01"), and the algorithm names
`Academic reference-profile corpus` throughout.

| # | Line | Cat | Current text (excerpt) | Proposed rewrite (excerpt) |
|---|---|---|---|---|
| M1 | L277 | b | "The **academic** covering-set size is P = 100 for the headline SGI experiments…" | "The **reference-profile** covering-set size is P = 100…" (applies to L386 and L536 too, which use "academic covering-set size" / "academic P") |

### §4 Empirical Results (L286–457)

| # | Line | Cat | Current text (excerpt) | Proposed rewrite (excerpt) |
|---|---|---|---|---|
| S1 | L399 | b | `\subsubsection{Curriculum Anchor Validation against CS2023 (CURR01)}` | `\subsubsection{Reference-Profile Anchor Validation against CS2023 (CURR01)}` |
| S2 | L402 | b | "Semantic coverage of CS2023 topics by **the academic top-500** is 30.4%…" | "…by **the reference-profile top-500** is 30.4%…" |
| S3 | L412 | b | caption: "…to **the academic top-500** (1,000 topic-level bootstrap resamples…)" | "…to **the reference-profile top-500**…" |
| S4 | L429 | b | caption: "Coverage: share of category-skill occurrences in **the academic profile**" | "…in **the reference profile**" |
| S5 | L432 | b | "…only 44.1% of its skill requirements appear in **the academic profile** lexically…" | "…appear in **the reference profile** lexically…" |
| S6 | L432 | a | "Semantic alignment reduces the **residual gap** in every category with a nonzero deficit…" | "…reduces the **residual reference-profile deficit** in every category…" |
| S7 | L463 | a c | "H1 (constructive alignment) is supported on the primary corpus…: technical categories carry the only nonzero deficits while soft skills are fully covered." | "H1, a constructive-alignment prediction about curricular coverage, is *consistent with* the measurements… we report consistency, not confirmation of the curricular claim." |
| S8 | L474 | a c | table row: `H1 & Constructive Alignment & Supported (ALIGN03, ALIGN04)` | `H1 & Constructive-alignment prediction & Consistent with measurements (ALIGN03, ALIGN04)` |

*L312, L384, L402-final ("it should not be read as representing the full
theoretical core") and L483 ("apparent gap", "estimated deficit") already conform.*

### §5 Discussion (L458–527)

| # | Line | Cat | Current text (excerpt) | Proposed rewrite (excerpt) |
|---|---|---|---|---|
| D1 | L485 | c d | `\subsection{Institutional Factors in Curriculum Adaptation}` | `\subsection{Institutional Factors: One Interpretation of the Measured Deficits}` |
| D2 | L487 | c | "…are consistent with---though do not by themselves establish---institutional constraints in curriculum adaptation" | *already hedged; keep, but append:* "…and are reported here as an interpretation, consistent with the audit framing." |
| D3 | L489 | c | "\textbf{Curriculum Governance and Accreditation:} Formal degree reviews and accreditation bodies operate on multi-year cycles (typically 3 to 6 years)." | add qualifier: "…a documented institutional mechanism offered as an interpretation of the measurements." |
| D4 | L489 | a | "Modifying course requirements or introducing new technical electives requires administrative and faculty committee approvals that lag industry tool adoption." | "…approvals that **may** lag industry tool adoption." |
| D5 | L494 | d | `\subsection{Implications and Recommendations}` | `\subsection{Implications of the Measurement Results}` |
| D6 | L496 | d | "We organize recommendations for higher education and accreditation around the empirical findings:" | "We separate what the measurements support from what would require evidence beyond this study; the latter are offered as questions for institutions, not as findings:" |
| D7 | L500 | d | "HEIs can address this by embedding modular, vendor-neutral technical modules… directly into existing operating systems and database courses." | "If the measured reference-profile deficit corresponds to a real curricular gap — an inference this study does not test — embedding modular, vendor-neutral technical modules… would be one response." |
| D8 | L501 | d | "The priority is therefore not new content but assessment: … departments should integrate oral presentations, collaborative design reviews, and peer code reviews directly into core computing courses." | "The measurement is silent on assessment practice; to the extent departments wish to revisit communication assessment, integrating oral presentations… is a common approach." |
| D9 | L506 | c d | "Accreditation bodies and professional societies (ACM, IEEE-CS) **should** issue regular modular addenda to curriculum guidelines to facilitate elective updates." | "…**could** issue regular modular addenda… a possibility this study's measurements motivate only indirectly." |
| D10 | L507 | d | "…educational authorities **should** maintain regional labor-market tracking to help institutions align elective offerings with local economic demand." | "…**could** maintain regional labor-market tracking; note the corpus is 85.2% US, so the evidence base for regional alignment outside the US is thin." |

*L500 first sentence and L501 first sentence already carry the
reference-profile qualifier and conform.*

### §5.6 Threats to Validity (L528–541)

Threats is in good shape — L533 ("drawn from 1,167 job postings … rather than
from institutionally collected syllabi") and L534 ("proxied through … reference
profiles rather than direct, institutionally mined university syllabi") both
conform, and L538 already says the deficits "should be read as *coverage* gaps
conditional on demand".

**One gap worth adding (no current sentence violates a category, but the section
is missing the sentence the title now implies):**

> **Recommended new item (T1):** "\textbf{Reference Profile Is Not a Curriculum
> Sample:} Every deficit reported here is the difference between a market corpus
> and a posting-derived reference profile. No university syllabus, course
> document or programme specification was collected or analysed, so these
> measurements do not establish the size — or the existence — of a curricular
> gap; CURR01 bounds the profile against CS2023 but does not convert the result
> into a curricular quantity."

### §6 Conclusion (L546–549)

| # | Line | Cat | Current text (excerpt) | Proposed rewrite (excerpt) |
|---|---|---|---|---|
| C1 | L549 | a b | "A substantial share of the apparent deficit reflects vocabulary divergence between **academic descriptors** and recruitment postings …, while **substantive residual gaps remain** concentrated in rapidly evolving technical areas…" | "…between **reference-profile descriptors** and recruitment postings …, while substantive residual **reference-profile** deficits remain concentrated in rapidly evolving technical areas — Cloud Infrastructure and Programming & Development. Whether those residuals correspond to curricular shortfalls is not established by this study." |
| C2 | L549 | d | "In practical terms, addressing **this divide** does not necessitate wholesale curriculum redesign." | "If the residual reference-profile deficits do correspond to curricular shortfalls, addressing them would not necessitate wholesale curriculum redesign — an inference we mark as conditional." |
| C3 | L549 | d | "Integrating modular credentials into established courses and assessing applied skills inside core courses offer feasible steps toward aligning academic preparation with contemporary workforce demands." | "Because the measurements cannot by themselves separate vocabulary divergence from curricular shortfall, the next step is a study that measures curricula directly; the modular-credential and assessment options in Section 5 remain candidate responses conditional on such evidence." |

*L549 sentence 1 ("which proxies academic skill requirements with an
employer-derived occupational reference profile rather than university
syllabi") and sentence 3 (the three-way instrument check, including "no human
line-by-line topic audit was performed") both conform and should be kept verbatim.*

---

## Sentences that already conform (keep these as the house style)

These are the patterns the rewrites above imitate:

- L70 abstract: "…by embedding coverage — a computational anchor, not a human
  audit — **so no curricular gap size is claimed**."
- L70 abstract: "**Reference-profile** deficits concentrate in Cloud
  Infrastructure (2.45 pp lexical, 0.94 pp semantic)…"
- L106: "a **posting-derived academic reference profile** (1,167 postings)"
- L132: "This distinction helps explain why **measured reference-profile
  deficits** concentrate in applied toolchains…"
- L218: "Academic skill requirements are represented using a standardized
  occupational--educational reference profile … **rather than scraped
  syllabi — a proxy** whose content validity is quantified against CS2023…"
- L384: "A single-sample instrument invites the objection that the **measured**
  gap is an artefact of one draw from the market."
- L483: "an **apparent** gap of 52.0% … reduce the **estimated** deficit to 32.0%"
- L487: "are consistent with — **though do not by themselves establish** —"
- L534: "Academic skill demands were **proxied** … rather than direct,
  institutionally mined university syllabi"
- L538: "the RQ3 deficits should be read as ***coverage*** **gaps conditional on
  demand** rather than as economy-wide demand shares"
- L549: "this empirical investigation — **which proxies academic skill
  requirements with an employer-derived occupational reference profile rather
  than university syllabi** — shows that profile--market misalignment is
  twofold."

---

## Note on consistency of the three gate-checked numbers

No rewrite above touches a number. Every quantitative constant cited here is
pinned by `audit/verify_claims.py` (103 checks) or by the render-integrity tests
added at `fbe9122`; if any rewrite is approved, those checks must be re-run
before commit, and for F2 the abstract word count must be re-checked against the
250-word cap.
