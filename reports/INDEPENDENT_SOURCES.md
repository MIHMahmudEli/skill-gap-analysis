# Step 1d Follow-up — Candidate Independent Market Sources

Date: 2026-10-12 · Branch: `q1-revision` · **No downloads performed.** Licenses and URLs
are recorded from established knowledge and must be re-verified at fetch time (web search
unavailable in the preparation environment; every row carries a re-verify flag).

Purpose: candidates that could provide evidence **independent of the LinkedIn scrape
family** (the entire HF Skill Gap pair is nested inside it — `datasets/OVERLAP_AUDIT.csv`),
as listed in `reports/PROVENANCE_AUDIT.md` §D. Nothing here has been downloaded or used.

## A. Technology-skill taxonomies (expert-curated, not postings)

| Source | Provenance | License (re-verify) | Unit type |
|---|---|---|---|
| O*NET 30.0 Database (`db_30_0`) — Tools & Technology / Skills / Knowledge sections | US Department of Labor, Employment and Training Administration; national occupational survey (biennial) | **CC BY 4.0** (verified 2026-10-13 at `onetcenter.org/license_db.html`; earlier "public domain" entry was wrong — attribution is mandatory; older releases may be used under this licence with the version number in the credit) | Occupation × tool/technology/skill statement |
| ESCO (European Skills, Competences, Qualifications and Occupations) v1.2+ | European Commission (JRC) + Cedefop; expert-mapped multilingual taxonomy | CC-BY 4.0 | Occupation/skill concept (stable ESCO IDs); includes technology-skill relations |
| Wikidata occupation→skill statements (P106, skills P101/P1068...) | Wikimedia community; crowdsourced structured data | CC0 | Structured subject–predicate–object statements (sparse, variable completeness) |

## B. Job-posting sources with a *different* collection mechanism

| Source | Provenance | License / ToS (re-verify) | Unit type |
|---|---|---|---|
| USAJOBS (US federal job openings) + API | US Office of Personnel Management; official government vacancy feed | Public domain content; API terms of use apply | Federal job announcement (title, agency, competencies, duties) |
| JobTech Development open API (Swedish Public Employment Service) | Arbetsförmedlingen (Swedish national employment service); public vacancy feed | Stated CC-BY 4.0 (verify at fetch) | Public-sector job vacancy (title, requirements, employer) |
| Adzuna job-search API (research access) | Private job aggregator (multi-source) | Free research tier with rate limits; redistribution rights limited (verify) | Aggregated vacancy (title, description, salary, category) |
| Kaggle/GitHub posting datasets scraped from Indeed/Glassdoor (various) | Unknown scrape pipelines, mostly individual authors | Typically labelled CC0 by uploaders, but underlying platform ToS likely prohibit redistribution (verify per dataset) | Scraped posting row; provenance audit mandatory before use |

## C. National-statistics / open-data anchors (aggregate, not postings)

| Source | Provenance | License (re-verify) | Unit type |
|---|---|---|---|
| BLS Occupational Employment and Wage Statistics (OEWS) | US Bureau of Labor Statistics; establishment survey | Public domain (US Gov) | Occupation × employment/wage estimate (aggregate) |
| BLS Employment Projections (2024–34) | US Bureau of Labor Statistics | Public domain | Occupation × projected growth/decline (aggregate) |
| Eurostat / EU Labour Force Survey skills module | Eurostat (EC) | CC-BY 4.0 (Eurostat reuse policy) | Country × labor-market/skills indicator (aggregate) |
| ILOSTAT | International Labour Organization | CC-BY 4.0 (verify) | Country × occupation/employment indicator (aggregate) |
| CBS Open Data (Statistics Netherlands) | Dutch national statistics office | CC-BY 4.0 (verify) | NL labor-market aggregates (supports the NL curriculum sample) |
| ONS Open Data (UK) | UK Office for National Statistics | Open Government Licence v3.0 | UK employment/skills aggregates |
| MoSPI / data.gov.in labor & skills datasets | India Ministry of Statistics and Programme Implementation | Open Government Data License v3.0 (verify) | India employment/skills aggregates (supports the India calibration claim) |

## Selection notes (for the author's decision)

1. **Directly comparable to the paper's estimand (posting-level skill requirements):**
   B, row 1–2 (official vacancy feeds — genuinely different collection mechanisms,
   public institutions, clean licensing). B rows 3–4 are aggregator scrapes with
   redistribution/ToS risk.
2. **Comparable to the taxonomy-level estimand (skill lists, not postings):** A, all rows.
   ESCO already serves as VALID01's gold standard; O*NET would add a second, US-anchored
   expert taxonomy that is fully independent of LinkedIn.
3. **Context/anchor only (aggregates, no skill strings):** C — usable to validate
   occupation-demand direction (e.g., 15-12xx growth) but cannot feed SGI matching.
4. All fetches require: license snapshot in `datasets/curriculum/license_snapshots/`
   style, a new manifest entry, and a new OVERLAP_AUDIT row for de-dup accounting.
