"""Phase 1 (CURR02 preparation): deterministic curriculum text extraction.

Reads the license-verified candidates in ``datasets/curriculum/MANIFEST.csv``
that have raw HTML snapshots under ``datasets/curriculum/raw/`` and produces
committed, phrase-level artifacts under ``datasets/curriculum/extracted/``:

  curriculum_phrases.csv      kept skill/content phrases per unit
  extraction_summary.json     per-unit counts + drop reasons + taxonomy hits
  validation_precision_100.csv  100-item stratified precision sample (seed 42)
  validation_recall_100.csv     100-item complementary recall sample (seed 42)

Design rules (frozen before any SGI is computed on this corpus):
  * Extraction is rule-based and content-region aware (per source template).
  * No analysis-driven selection: filters are boilerplate/length only.
  * Only phrases (<=500 chars) are committed; no full course prose.
  * Source-depth caveat: a few MIT OCW units resolved to the course landing
    page rather than its syllabus sub-page, so they contribute only the
    Course Description + Topics taxonomy labels. A low phrase count there
    means a thin source page, not a parser miss; it is recorded per unit in
    extraction_summary.json and is a documented corpus limitation.
  * Human validation gate: CURR02 does NOT run until the author labels or
    waives the two validation CSVs (SELECTION_PROTOCOL.md sec 7.4).

Usage:  python datasets/curriculum/extract_units.py
"""
from __future__ import annotations

import ast
import csv
import html
import json
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURR = ROOT / "datasets" / "curriculum"
RAW = CURR / "raw"
OUT = CURR / "extracted"
MANIFEST = CURR / "MANIFEST.csv"
TAXONOMY_JSON = CURR / "taxonomy8.json"
ALIGN03 = ROOT / "experiments" / "exp_scripts" / "align03_domain_gap.py"

SEED = 42
MIN_CHARS = 40
MIN_TOPIC_CHARS = 12   # syllabus/topic list items may be short
MAX_CHARS = 500
PRECISION_N = 100
RECALL_N = 100

# --- boilerplate filters (documented drop reasons) -------------------------
LICENSE_RE = re.compile(
    r"licensed under a creative commons|all rights reserved|"
    r"except where otherwise noted|under a creative commons attribution",
    re.I,
)
COOKIE_RE = re.compile(r"cookie|privacy overview|save & accept|consent", re.I)
SOCIAL_TOKENS = (
    "facebook", "twitter", "linkedin", "instagram", "youtube", "pinterest",
    "tiktok", "bluesky", "soundcloud", "spotify", "reddit", "threads", "mastodon",
)
SHARE_PREFIX_RE = re.compile(r"^(share|follow us|subscribe|back to top|menu)\b", re.I)
LOGISTICS_RE = re.compile(
    r"verified certificate|professional certificate|transfer credit|enroll|"
    r"edX|sign up|audit the course|how to take this course|how to teach this course|"
    r"watch an introduction|follow this workflow|puzzle day|discussion forum|"
    r"study load|course coordinator|give now|newsletter|donate|buy merchandise",
    re.I,
)
CONTACT_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|contact us|sitemap|accessibility", re.I)

# Stanford SEE player chrome: the lecture title, a "Watch Online/Download"
# control cluster, and the lecture's Topics list are all one text node. The
# controls are boilerplate, but the Topics list after them is genuine syllabus
# content. Instead of dropping the whole sentence (which silently discards
# recoverable curriculum content and shows up as a recall defect), drop only the
# control cluster up to and including the "Topics:" marker and keep the list,
# preserving the marker as context so a human rater can see where the text came
# from. Applied only when a Topics marker is present; a chrome-only sentence
# (no Topics) is left intact so MEDIA_RE still classifies it as media_chrome.
STANFORD_CHROME_RE = re.compile(
    r"^(.*?(?:Watch Online|Download|Duration|Watch Now).*?)(Topics:\s*)", re.I | re.DOTALL,
)

# Sections that carry curriculum content even when the phrase is short
# (syllabus/topic list items such as "04. Divide and conquer").
TOPIC_SECTION_RE = re.compile(
    r"topic|subject|syllab|overview|description|prerequisit|learning|"
    r"course content|content|what you|module|lecture|unit|program|goal|objective",
    re.I,
)
# Sections that are pure page metadata -> drop everything under them.
METADATA_SECTION_RE = re.compile(
    r"^\s*(instructor|department|course info|class meeting|contact|"
    r"calendar|schedule|staff|acknowledg|license|related course|"
    r"resource|download|newsletter|subscribe|donate|share|footer|menu)\b",
    re.I,
)
# Media-player / download chrome (Stanford SEE lecture pages).
MEDIA_RE = re.compile(
    r"right click|watch online|save as|watch now|download \d+ min|"
    r"^\s*duration\s*:|^\s*watch\s*$|^\s*download\s*$", re.I,
)
# Assessment logistics (how the course is graded), not curriculum skill
# content. Deliberately avoids 'prerequisite': prerequisite statements carry
# real skill content and must be kept.
ASSESSMENT_RE = re.compile(
    r"midterm|final exam|final test|in-class exam|there will be|"
    r"homework \d|problem sets?\b|solutions lecture|exam solutions|"
    r"grades? will|\bgrading\b|due date|submit your|assignment \d|"
    r"comprehensive final|two in-class|letter grade|regardless of prerequisit|"
    r"strongly caution|evaluate your understanding", re.I,
)

# container / skip rules keyed by hostname substrings
SKIP_TAGS = {"script", "style", "noscript", "header", "footer", "nav", "aside", "form"}
SKIP_CLASS_RE = re.compile(
    r"cookie|consent|navbar|menu|footer|sidebar|social|breadcrumb|pagination|modal|"
    r"dropdown|newsletter|share|banner|skip-link|offcanvas|drawer|master-navigation|"
    r"site-info|licen[cs]e|related|discussion|subscribe",
    re.I,
)
BLOCK_TAGS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "dt", "dd", "figcaption"}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
CONTAINER_ID_RE = re.compile(r"course-main-content|course-content-section", re.I)


class PageParser(HTMLParser):
    """Shared state for the scoped parser below."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.container_depth = 0          # >0 while inside a content container
        self.container_seen = False
        self.buf: list[str] = []
        self.section = ""
        self.container_blocks: list[tuple[str, str]] = []  # (section, text)
        self.body_blocks: list[tuple[str, str]] = []
        self.meta_description = ""
        self._heading_buf: list[str] | None = None

    @staticmethod
    def _attrs(attrs) -> dict:
        return {k.lower(): (v or "") for k, v in attrs}

    def _flush(self) -> None:
        if self.buf:
            text = re.sub(r"\s+", " ", " ".join(self.buf)).strip()
            self.buf = []
            if text:
                target = self.container_blocks if self.container_depth else self.body_blocks
                target.append((self.section, text))


class ScopedPageParser(PageParser):
    """Captures block-level text inside content containers (with fallback),
    using an explicit open-tag stack for correct depth accounting."""

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[tuple[str, bool, bool]] = []  # (tag, is_skip, is_container)

    def handle_starttag(self, tag, attrs):
        a = self._attrs(attrs)
        cls_id = f"{a.get('class', '')} {a.get('id', '')}"
        is_skip = tag in SKIP_TAGS or bool(SKIP_CLASS_RE.search(cls_id))
        is_container = (not is_skip) and (
            bool(CONTAINER_ID_RE.search(a.get("id", "")))
            or (tag in ("main", "article"))
            or (tag == "div" and "master-content" in cls_id)
        )
        if is_container and self.container_depth == 0:
            self._flush()
        self.stack.append((tag, is_skip, is_container))
        if is_skip:
            self.skip_depth += 1
            return
        if is_container:
            self.container_depth += 1
            self.container_seen = True
        if tag == "meta" and a.get("name", "").lower() == "description":
            # Meta content is an attribute value, so HTMLParser does not decode
            # embedded markup; Stanford SEE descriptions carry literal <br>
            # runs. Decode entities and normalize breaks to plain spaces.
            desc = html.unescape(a.get("content", ""))
            desc = re.sub(r"<\s*br\s*/?\s*>", " ", desc, flags=re.I)
            self.meta_description = re.sub(r"\s+", " ", desc).strip()
        # <br> produces no text node but must separate adjacent text runs,
        # otherwise words (and embedded markers) run together.
        if tag == "br" and self.buf:
            self.buf.append(" ")
        if tag in BLOCK_TAGS:
            self._flush()
            if tag in HEADING_TAGS:
                self._heading_buf = []
        if tag == "div" and "heading" in a.get("class", "").lower():
            self._flush()
            self._heading_buf = []

    def handle_endtag(self, tag):
        if tag in HEADING_TAGS or (self._heading_buf is not None and tag == "div"):
            if self._heading_buf is not None:
                heading = re.sub(r"\s+", " ", " ".join(self._heading_buf)).strip()
                if heading and len(heading) <= 100:
                    self.section = heading
            self._heading_buf = None
        if tag in BLOCK_TAGS:
            self._flush()
        # pop stack until matching tag (HTML is not perfectly nested; bounded pop)
        for i in range(len(self.stack) - 1, -1, -1):
            t, is_skip, is_container = self.stack[i]
            if t == tag:
                for _, s2, c2 in self.stack[i:]:
                    if s2:
                        self.skip_depth = max(0, self.skip_depth - 1)
                    if c2:
                        self.container_depth = max(0, self.container_depth - 1)
                        if self.container_depth == 0:
                            self._flush()
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self._heading_buf is not None:
            self._heading_buf.append(data)
            return
        if data.strip():
            self.buf.append(data)

    def close(self):
        self._flush()
        super().close()


def load_taxonomy() -> dict[str, list[str]]:
    """Extract SKILL_CATEGORIES from ALIGN03 (single source of truth)."""
    src = ALIGN03.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if getattr(tgt, "id", "") == "SKILL_CATEGORIES":
                    return ast.literal_eval(node.value)
    raise RuntimeError("SKILL_CATEGORIES not found in align03_domain_gap.py")


def compile_taxonomy_matcher(taxonomy: dict[str, list[str]]):
    """Return fn(phrase_lower) -> list[(category, term)] (longest-term wins)."""
    compiled: list[tuple[str, str, re.Pattern]] = []
    for cat, terms in taxonomy.items():
        for term in terms:
            t = term.lower().strip()
            if not t:
                continue
            if re.fullmatch(r"[a-z0-9+#.]{1,3}", t):
                pat = re.compile(rf"(?<![a-z0-9+.#]){re.escape(t)}(?![a-z0-9])")
            else:
                pat = re.compile(re.escape(t))
            compiled.append((cat, t, pat))
    compiled.sort(key=lambda x: -len(x[1]))

    def match(phrase_lower: str):
        hits, seen_terms = [], set()
        for cat, term, pat in compiled:
            if term in seen_terms:
                continue
            if pat.search(phrase_lower):
                hits.append((cat, term))
                seen_terms.add(term)
                if len(hits) >= 8:
                    break
        return hits

    return match


def _norm_section(section: str) -> str:
    """Fold a heading to its head term: drop parentheticals and trailing 's'."""
    s = re.split(r"[\(:]", section or "")[0].strip()
    s = re.sub(r"(?<=\w)s$", "", s)          # Instructors->Instructor, Departments->Department
    return s


def split_sentences(text: str) -> list[str]:
    """Split a block into phrases, each <= MAX_CHARS.

    Three passes, because prose splits cleanly but tabular/list content often
    has no sentence boundary at all:
      1. sentence boundaries (". " followed by a capital);
      2. clause boundaries ("; " / ", " -- where Stanford's Topics lists and
         handout tables actually break);
      3. hard word-boundary cut, as a last resort (a single run-on token
         longer than the cap, e.g. an unwrapped asset filename).

    Without passes 2-3, a period-free 900-char handout table survives as one
    "sentence" and violates the documented MAX_CHARS contract.
    """
    if len(text) <= MAX_CHARS:
        return [text]
    out: list[str] = []
    for part in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text):
        part = part.strip()
        if not part:
            continue
        if len(part) <= MAX_CHARS:
            out.append(part)
            continue
        # pass 2: pack clauses up to the cap
        buf = ""
        for clause in re.split(r"(?<=[;,])\s+", part):
            if buf and len(buf) + len(clause) + 1 > MAX_CHARS:
                out.append(buf)
                buf = clause
            else:
                buf = f"{buf} {clause}".strip()
        if buf:
            out.append(buf)
    # pass 3: hard cut anything still over the cap
    final: list[str] = []
    for part in out:
        while len(part) > MAX_CHARS:
            cut = part.rfind(" ", 0, MAX_CHARS)
            if cut <= 0:
                cut = MAX_CHARS
            final.append(part[:cut].strip())
            part = part[cut:].strip()
        if part:
            final.append(part)
    return final


def drop_reason(phrase: str, section: str = "") -> str | None:
    """Return drop-reason code or None to keep the phrase.

    ``section`` is the nearest preceding heading. It controls the length gate:
      * pure page-metadata sections (Instructors, Departments, ...) are dropped
        outright, since they never carry curriculum skill content;
      * curriculum sections (Topics, Syllabus, Overview, ...) accept short
        list items such as "04. Divide and conquer", which are real syllabus
        content and must not be discarded by the generic MIN_CHARS gate.
    """
    if METADATA_SECTION_RE.search(_norm_section(section)):
        return "metadata_section"
    # generic OCW taxonomy labels ("Departments: Mathematics") are page
    # metadata, not curriculum skill content
    if re.fullmatch(r"(mathematics|computer science|engineering|science)", phrase.strip(), re.I):
        return "metadata_section"
    # syllabus/topic list items are meaningful even when short
    eff_min = MIN_TOPIC_CHARS if TOPIC_SECTION_RE.search(section or "") else MIN_CHARS
    if len(phrase) < eff_min:
        return "too_short"
    if len(phrase) > MAX_CHARS * 2:
        return "too_long"
    if LICENSE_RE.search(phrase):
        return "license_boilerplate"
    if COOKIE_RE.search(phrase):
        return "cookie_privacy"
    if SHARE_PREFIX_RE.match(phrase):
        return "nav_share"
    if MEDIA_RE.search(phrase):
        return "media_chrome"
    if ASSESSMENT_RE.search(phrase):
        return "assessment_logistics"
    low = phrase.lower()
    social_hits = sum(1 for t in SOCIAL_TOKENS if t in low)
    if social_hits >= 3:
        return "social_nav"
    if LOGISTICS_RE.search(phrase):
        return "enrollment_logistics"
    if CONTACT_RE.search(phrase):
        return "contact_info"
    return None


def extract_unit(unit_id: str, html_path: Path, match_fn):
    html = html_path.read_text(encoding="utf-8", errors="replace")
    parser = ScopedPageParser()
    parser.feed(html)
    parser.close()
    blocks = parser.container_blocks if len(parser.container_blocks) >= 3 else parser.body_blocks
    if parser.meta_description:
        blocks = [("Page meta description", parser.meta_description)] + blocks

    kept, dropped = [], Counter()
    seen = set()
    full_pool = []  # dicts: phrase, section, is_extracted, drop_reason
    for section, block in blocks:
        for sent in split_sentences(block):
            sent = re.sub(r"^\s*(?:[-•*\d]+[.)]\s*|week\s+\d+\s*[:\-]?\s*)", "", sent).strip()
            # Stanford SEE: recover the Topics list embedded after player chrome,
            # keeping the "Topics:" marker so a rater can trace the provenance.
            m = STANFORD_CHROME_RE.match(sent)
            if m:
                sent = (m.group(2) + sent[m.end():]).strip()
            reason = drop_reason(sent, section)
            key = re.sub(r"\W+", "", sent.lower())
            if reason is None and (not key or key in seen):
                reason = "duplicate"
            if reason:
                dropped[reason] += 1
                # All drop reasons enter the recall pool, including too_short:
                # it is the single largest drop class, so excluding it would
                # make a recall estimate structurally impossible (the sampler
                # would fall back to metadata/duplicate padding instead).
                full_pool.append({"phrase": sent, "section": section,
                                  "is_extracted": 0, "drop_reason": reason})
                continue
            seen.add(key)
            hits = match_fn(sent.lower())
            kept.append(
                {
                    "unit_id": unit_id,
                    "section": section,
                    "phrase": sent,
                    "n_chars": len(sent),
                    "taxonomy_hits": ";".join(f"{c}:{t}" for c, t in hits),
                    "n_taxonomy_hits": len(hits),
                }
            )
            full_pool.append({"phrase": sent, "section": section,
                              "is_extracted": 1, "drop_reason": ""})
    return kept, dropped, full_pool, len(blocks)


def stratified_sample(items, n, strata_fn, seed=SEED, allocation="proportional"):
    """Stratified random sample (seeded, deterministic).

    allocation="proportional": each stratum gets n * N_h / N items (used for
        the precision sample, where every kept phrase is exchangeable and we
        want the sample to mirror the corpus composition).
    allocation="equal": each non-empty stratum gets ~n / H items regardless
        of its size (used for the recall sample, where drop classes differ by
        an order of magnitude -- proportional allocation would spend ~58 of
        100 items on the single largest class and leave the other drop rules
        unvalidated). Unmet quota from undersized strata round-robins to
        strata that still have capacity.
    """
    rng = random.Random(seed)
    groups = defaultdict(list)
    for it in items:
        groups[strata_fn(it)].append(it)
    if allocation == "equal":
        quota = {k: 0 for k in sorted(groups)}
        active = [k for k in sorted(groups) if groups[k]]
        remaining = n
        while remaining > 0 and active:
            progressed = False
            for k in active:
                if remaining == 0:
                    break
                if quota[k] < len(groups[k]):
                    quota[k] += 1
                    remaining -= 1
                    progressed = True
            if not progressed:
                break
            active = [k for k in active if quota[k] < len(groups[k])]
        base = quota
    else:
        total = len(items)
        quotas = {k: (len(v) * n) / total for k, v in groups.items()}
        base = {k: int(q) for k, q in quotas.items()}
        rem = n - sum(base.values())
        order = sorted(quotas, key=lambda k: -(quotas[k] - base[k]))
        for k in order[:rem]:
            base[k] += 1
    sample = []
    for k, v in groups.items():
        rng.shuffle(v)
        sample.extend(v[: base[k]])
    rng.shuffle(sample)
    return sample


def _sum_drop_reasons(summary_units: list[dict]) -> dict[str, int]:
    """Sum per-unit drop counters across all units.

    NOTE: a dict comprehension ({k: v for u in ... for k, v in ...}) silently
    overwrites when two units share a drop reason; a Counter update sums.
    """
    total: Counter = Counter()
    for u in summary_units:
        total.update(u["dropped"])
    return dict(sorted(total.items(), key=lambda kv: -kv[1]))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    taxonomy = load_taxonomy()
    TAXONOMY_JSON.write_text(
        json.dumps(taxonomy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    match_fn = compile_taxonomy_matcher(taxonomy)

    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    extractable = [
        r for r in rows
        if r["extraction_status"] in ("pending", "extracted")
        and (RAW / f"{r['unit_id']}.html").exists()
    ]
    all_kept, summary_units, all_pool = [], [], []
    inst_phrase_counts = Counter()
    for r in extractable:
        uid = r["unit_id"]
        kept, dropped, pool, n_blocks = extract_unit(uid, RAW / f"{uid}.html", match_fn)
        for k in kept:
            inst_phrase_counts[r["institution"]] += 1
        all_kept.extend(
            dict(k, institution=r["institution"], stratum=r["stratum"],
                 level=r["level"], vintage_group=r["vintage_group"],
                 source_url=r["source_url"], material_year=r["material_year"])
            for k in kept
        )
        all_pool.extend(dict(p, unit_id=uid, institution=r["institution"],
                             vintage_group=r["vintage_group"])
                        for p in pool)
        summary_units.append(
            {
                "unit_id": uid,
                "institution": r["institution"],
                "vintage_group": r["vintage_group"],
                "blocks": n_blocks,
                "phrases_kept": len(kept),
                "phrases_with_taxonomy_hit": sum(1 for k in kept if k["n_taxonomy_hits"]),
                "dropped": dict(dropped),
            }
        )
        print(f"{uid:>14}  blocks={n_blocks:>3}  kept={len(kept):>3}  "
              f"tax_hits={summary_units[-1]['phrases_with_taxonomy_hit']:>3}  "
              f"dropped={sum(dropped.values())}")

    # committed phrase table (deterministic order: manifest order, then position)
    order = {r["unit_id"]: i for i, r in enumerate(rows)}
    all_kept.sort(key=lambda k: (order.get(k["unit_id"], 999),))
    fields = ["unit_id", "institution", "stratum", "level", "vintage_group",
              "material_year", "section", "phrase", "n_chars",
              "taxonomy_hits", "n_taxonomy_hits", "source_url"]
    with (OUT / "curriculum_phrases.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_kept)

    # validation samples (author-gated; CURR02 blocked until labelled/waived)
    def strata_prec(it):
        return (it["vintage_group"] == "modern", it["stratum"])

    prec = stratified_sample(all_kept, PRECISION_N, strata_prec, SEED)
    prec_fields = ["item_id", "unit_id", "institution", "vintage_group", "stratum",
                   "section", "phrase", "taxonomy_hits", "rater_label", "rater_notes"]
    with (OUT / "validation_precision_100.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=prec_fields)
        w.writeheader()
        for i, it in enumerate(prec, 1):
            w.writerow({
                "item_id": f"P{i:03d}", "unit_id": it["unit_id"],
                "institution": it["institution"], "vintage_group": it["vintage_group"],
                "stratum": it["stratum"], "section": it["section"],
                "phrase": it["phrase"], "taxonomy_hits": it["taxonomy_hits"],
                "rater_label": "", "rater_notes": "",
            })

    # recall: complementary sample = sentences the filters dropped. Design:
    # a stratified random sample over ALL drop reasons (including too_short
    # and metadata/duplicate) with EQUAL allocation across (vintage_group,
    # drop_reason) cells, so every drop rule gets validation coverage instead
    # of the sample collapsing onto whichever class is largest. Cell sizes are
    # recorded in extraction_summary.json, so a design-weighted estimate
    #   recall = 1 - sum_c (N_c / N) * (wrongly_dropped_c / n_c)
    # is computable from this file plus the rater labels alone.
    dropped_pool = [p for p in all_pool if not p["is_extracted"]]
    recall = stratified_sample(
        dropped_pool, min(RECALL_N, len(dropped_pool)),
        lambda p: (p["vintage_group"], p["drop_reason"]),
        SEED, allocation="equal",
    )
    stratum_sizes = Counter(
        (p["vintage_group"], p["drop_reason"]) for p in dropped_pool
    )
    recall_design = {
        "allocation": "equal across (vintage_group, drop_reason) cells",
        "seed": SEED,
        "population_n": len(dropped_pool),
        "sample_n": len(recall),
        "stratum_population_sizes": {
            f"{v}|{r}": c for (v, r), c in sorted(stratum_sizes.items())
        },
        "weighting_note": ("design-weighted recall = 1 - sum_c (N_c/N) * "
                           "(wrong_c / n_c); N_c from stratum_population_sizes, "
                           "n_c = sampled count per cell in this CSV"),
    }
    rec_fields = ["item_id", "unit_id", "institution", "vintage_group",
                  "section", "phrase", "drop_reason", "is_extracted",
                  "rater_label", "rater_notes"]
    with (OUT / "validation_recall_100.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rec_fields)
        w.writeheader()
        for i, p in enumerate(recall, 1):
            w.writerow({
                "item_id": f"R{i:03d}", "unit_id": p["unit_id"],
                "institution": p["institution"], "vintage_group": p["vintage_group"],
                "section": p["section"], "phrase": p["phrase"],
                "drop_reason": p["drop_reason"], "is_extracted": p["is_extracted"],
                "rater_label": "", "rater_notes": "",
            })

    modern = [r for r in rows if r["extraction_status"] in ("pending", "extracted")
              and r["vintage_group"] == "modern" and (RAW / f"{r['unit_id']}.html").exists()]
    by_inst = Counter(r["institution"] for r in modern)
    summary = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%Z"),
        "seed": SEED,
        "min_chars": MIN_CHARS,
        "max_chars": MAX_CHARS,
        "units_extracted": len(summary_units),
        "phrases_kept_total": len(all_kept),
        "phrases_with_taxonomy_hit": sum(1 for k in all_kept if k["n_taxonomy_hits"]),
        "drop_reasons_total": _sum_drop_reasons(summary_units),
        "precision_design": {
            "allocation": "proportional across (vintage_group, stratum) cells",
            "seed": SEED,
            "sample_n": len(prec),
            "population_n": len(all_kept),
        },
        "recall_design": recall_design,
        "modern_candidate_units": len(modern),
        "modern_by_institution": dict(by_inst),
        "taxonomy_source": "experiments/exp_scripts/align03_domain_gap.py::SKILL_CATEGORIES",
        "units": summary_units,
        "human_validation_gate": {
            "precision_sample": "validation_precision_100.csv",
            "recall_sample": "validation_recall_100.csv",
            "status": "AWAITING_AUTHOR_LABELLING_OR_WAIVER",
            "note": "CURR02 must not run until these are labelled or waived "
                    "(SELECTION_PROTOCOL.md section 7, step 4)",
        },
    }
    (OUT / "extraction_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # manifest status update: pending -> extracted
    changed = 0
    extracted_ids = {u["unit_id"] for u in summary_units}
    for r in rows:
        if r["unit_id"] in extracted_ids and r["extraction_status"] == "pending":
            r["extraction_status"] = "extracted"
            changed += 1
        if r["extraction_status"] == "backup_applied":
            # never activated (no SWAP_LOG entry, no download); reclassify
            r["extraction_status"] = "backup_unused"
            r["notes"] = (r["notes"] + "; reclassified backup_applied->backup_unused "
                          "2026-10-11: no swap executed (SWAP_LOG empty), no download")
            changed += 1
    with MANIFEST.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\nkept {len(all_kept)} phrases from {len(summary_units)} units; "
          f"manifest rows updated: {changed}")
    print(f"precision sample {len(prec)}; recall sample {len(recall)} "
          f"(author gate: AWAITING LABELLING)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
