"""ALIGN06 - O*NET x BLS OEWS employment-weighted tech-skill demand profile.

Pre-registration: ``experiments/ALIGN06_PREREG.md`` (every section binding).

Section 2.2 firewall, which is why this file is shaped the way it is:

  * The measurement instrument -- academic reference profile, lexical matcher,
    semantic matcher (all-MiniLM-L6-v2, cosine >= tau) and ``SGI = 1 -
    coverage`` -- is **imported** from the SENS01/ALIGN01/02 code path and is
    never rewritten here.  ``load_instruments()`` executes that module by path
    and the grid calls *its* functions.
  * ALIGN06 adds exactly one new thing: ``build_market_profile()``, which
    builds a market profile from O*NET + OEWS instead of from postings.
  * The eight-category taxonomy is imported from ALIGN03 and is used **only**
    for the section 6.3 report; it never filters the profile.
  * No posting row enters profile construction.  Postings are read only by the
    section 6.1 control (a separate script, already passed) and by the section
    6.4 descriptive cross-source comparison.

Outputs (section 8), all under ``results/ALIGN06_onet_demand_profile/``::

    metrics.json, table_sgi_onet_grid.csv, table_category_gap_onet.csv,
    table_onet_profile_top.csv, table_cross_source.csv

Usage::

    python experiments/align06_demand_profile.py            # full run
    python experiments/align06_demand_profile.py --selftest # no OEWS needed

Exit: 0 = completed, 1 = refused (missing/invalid input or failed 6.1 control).
The selftest never writes into results/ -- it exists only to prove the code
path runs, and its numbers are not preregistration results.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import string
import sys
import time
import unicodedata
import zipfile
from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
SENS01_PATH = ROOT / "experiments" / "exp_scripts" / "sens01_sgi_sensitivity.py"
ALIGN03_PATH = ROOT / "experiments" / "exp_scripts" / "align03_domain_gap.py"
OUT_DIR = ROOT / "results" / "ALIGN06_onet_demand_profile"

RAW_DIR = ROOT / "datasets" / "onet" / "raw"
ONET_ZIP = RAW_DIR / "db_30_0_text.zip"
ONET_DIR = RAW_DIR / "db_30_0" / "db_30_0_text"
OEWS_ZIP = RAW_DIR / "oesm25nat.zip"
EMB_CACHE = ROOT / "datasets" / "onet" / "emb_cache"

CONTROL_JSON = OUT_DIR / "control_6_1.json"
LIC_SNAPSHOT_DIR = ROOT / "datasets" / "curriculum" / "license_snapshots"

# ---------------------------------------------------------------------------
# Preregistered constants (ALIGN06_PREREG.md 3, 4, 5, 6 -- fixed before fetch)
# ---------------------------------------------------------------------------

SEED = 42
K_GRID = [50, 100, 200, 500]
P_GRID = [100, 250, 500, 1000]          # plus the P = "all" anchor row set
TAUS = [0.4, 0.5, 0.6, 0.7]
B_SKILL = 1000                          # 5: CI_skill
B_OCC = 500                             # 5: CI_occ
B_OCC_CAT = 1000                        # 6.3: category deficit bootstrap
PROFILE_N = 500
MODEL_NAME = "all-MiniLM-L6-v2"

ONET_RELEASE_EXPECTED = "O*NET 30.0"     # 3: verified against Read Me.txt

# 4.1 secondary stratum: the 16 SOC 2018 detailed codes frozen verbatim in
# experiments/ALIGN05_PREREG.md section 4 (no new code list is authored here).
TECH_SOC = [
    "15-1211", "15-1212", "15-1213", "15-1216", "15-1221", "15-1231",
    "15-1241", "15-1244", "15-1251", "15-1252", "15-1253", "15-1254",
    "15-1255", "15-1256", "15-2051", "11-3021",
]

# 4.5 fixed robustness variants; "economy-wide" is the primary/headline stratum.
VARIANT_ORDER = ["economy-wide", "computing-IT", "commodity-title",
                 "unweighted", "importance-weighted"]

# 4.3 strip set for *surrounding* punctuation and trademark markers.  Narrow on
# purpose: '+ # . / - & _' are semantically part of technology names ('c++',
# 'c#', '.net', 'f#', 'node.js'), so stripping them would silently corrupt the
# vocabulary.  Recorded verbatim in metrics.json so the choice is auditable
# rather than implicit.
_KEEP_IN_TOKEN = set("+#/-&_")
_STRIP_CHARS = "".join(
    ch for ch in (string.punctuation + "\u00ae\u2122\u00a9\u2018\u2019"
                  "\u201c\u201d\u2026\u00ab\u00bb")
    if ch not in _KEEP_IN_TOKEN
)

_WS = re.compile(r"\s+")

SENS01 = None
ALIGN03 = None
_MODEL = None


def log(msg: str) -> None:
    print(msg, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _import_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"FATAL: cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# 4.3 skill string normalization (fixed before fetch)
# ---------------------------------------------------------------------------

def normalize(raw) -> str:
    """NFKC -> case-fold -> collapse whitespace -> strip surrounding
    punctuation and trademark markers (section 4.3, in that order).

    A leading '.' is preserved when it starts a word character ('.net',
    '.asp'): the strip step would otherwise eat it, and the posting corpora
    spell the framework '.net', not 'net'.  A trailing '.' is stripped like
    any other surrounding punctuation.
    """
    if raw is None:
        return ""
    if isinstance(raw, float) and math.isnan(raw):
        return ""
    s = unicodedata.normalize("NFKC", str(raw))
    s = s.casefold()
    s = _WS.sub(" ", s).strip()
    lead_dot = s.startswith(".") and len(s) > 1 and s[1].isalnum()
    if lead_dot:
        s = s[1:]
    prev = None
    while s and s != prev:
        prev = s
        s = s.strip(_STRIP_CHARS).strip()
    if lead_dot and s:
        s = "." + s
    return s


# ---------------------------------------------------------------------------
# 4.2 employment weight and code crosswalk
# ---------------------------------------------------------------------------

def soc_base(onet_soc_code: str) -> str:
    """'15-1252.00' / '15-1252.01' -> '15-1252' (SOC 2018 six-digit base)."""
    return str(onet_soc_code).split(".")[0].strip()


def load_oews(zip_path: Path) -> tuple[dict[str, float], dict]:
    """Read the OEWS national workbook out of the archive.

    Returns {OCC_CODE: TOT_EMP} for the *detailed* occupation group only, plus
    a provenance dict (inner workbook, sheet, suppression counts).
    """
    with zipfile.ZipFile(zip_path) as zf:
        members = [n for n in zf.namelist()
                   if n.lower().endswith((".xlsx", ".xls", ".csv"))
                   and not n.split("/")[-1].startswith("~")]
        if not members:
            raise SystemExit(f"FATAL: no spreadsheet inside {zip_path.name}")
        # The national file carries 'nat' in its name; prefer it deterministically.
        members.sort(key=lambda n: (0 if "nat" in n.lower() else 1, n))
        inner = members[0]
        blob = zf.read(inner)

    if inner.lower().endswith(".csv"):
        sheets = {"csv": pd.read_csv(BytesIO(blob), header=None, dtype=object)}
    else:
        sheets = pd.read_excel(BytesIO(blob), sheet_name=None,
                               header=None, dtype=object)

    chosen = None
    for sheet_name in sorted(sheets):
        df = sheets[sheet_name]
        hdr_i, cols = None, None
        for i in range(min(40, len(df))):
            vals = ["" if pd.isna(v) else str(v).strip().upper()
                    for v in df.iloc[i].tolist()]
            if "OCC_CODE" in vals and "TOT_EMP" in vals:
                hdr_i, cols = i, vals
                break
        if hdr_i is None:
            continue
        body = df.iloc[hdr_i + 1:].copy()
        body.columns = cols
        body = body[body["OCC_CODE"].notna()]
        if len(body):
            chosen = (sheet_name, body, cols, hdr_i)
            break

    if chosen is None:
        raise SystemExit(
            f"FATAL: no sheet in {inner} carries an OCC_CODE/TOT_EMP header")

    sheet_name, body, cols, hdr_i = chosen
    occ_code = body["OCC_CODE"].astype(str).str.strip()
    tot_emp = pd.to_numeric(body["TOT_EMP"], errors="coerce")

    detail = pd.Series(True, index=body.index)
    if "O_GROUP" in cols:
        grp = body["O_GROUP"].astype(str).str.strip().str.lower()
        detail = grp == "detailed"

    matched = detail & occ_code.notna() & (occ_code != "") & tot_emp.notna()
    suppressed = detail & occ_code.notna() & (occ_code != "") & tot_emp.isna()

    out: dict[str, float] = {}
    for code, val in zip(occ_code[matched], tot_emp[matched]):
        out[str(code)] = float(val)

    prov = {
        "inner_workbook": inner,
        "sheet": str(sheet_name),
        "header_row_0based": int(hdr_i),
        "o_group_filter": "detailed" if "O_GROUP" in cols else "none",
        "rows_detailed": int(detail.sum()),
        "rows_detailed_suppressed": int(suppressed.sum()),
        "rows_detailed_matched": int(len(out)),
        "suppressed_note": ("`**` / `-` TOT_EMP cells are suppressed or absent; "
                            "they are dropped, never zero-weighted (4.2)"),
    }
    return out, prov


# ---------------------------------------------------------------------------
# 4.1 / 4.3 / 4.4 -- the one new function ALIGN06 is allowed to add
# ---------------------------------------------------------------------------

class MarketProfile:
    """An occupation frame plus its skill vocabulary and demand weights."""

    __slots__ = ("name", "string_field", "occ_codes", "w", "sk_idx", "sk_wt",
                 "vocab", "vocab_list", "n_before_dedup", "n_after_dedup",
                 "example_empty", "commodity_fallback")

    def __init__(self, name: str, string_field: str) -> None:
        self.name = name
        self.string_field = string_field
        self.occ_codes: list[str] = []
        self.w: np.ndarray = np.zeros(0, np.float64)
        self.sk_idx: list[np.ndarray] = []
        self.sk_wt: list[np.ndarray] = []
        self.vocab: dict[str, int] = {}
        self.vocab_list: list[str] = []
        self.n_before_dedup = 0
        self.n_after_dedup = 0
        self.example_empty = 0
        self.commodity_fallback = 0

    @property
    def n_occ(self) -> int:
        return len(self.occ_codes)


def employment_multiplicity(frame: list[str],
                            oews: dict[str, float]) -> dict:
    """Quantify the §4.2 crosswalk's many-O*NET-codes-to-one-OEWS-line effect.

    Section 4.2 says to truncate to the SOC six-digit base and join on
    OCC_CODE, which gives every O*NET-SOC code sharing a base that base's full
    TOT_EMP.  67 of the frame's bases are shared, so the join inflates
    sum_o w(o) relative to counting each base once.  Implemented literally as
    preregistered; measured and disclosed here so a reader can judge it.
    """
    bases = [soc_base(c) for c in frame]
    counts = Counter(bases)
    multi = {b: n for b, n in sorted(counts.items()) if n > 1}
    joined = float(sum(oews.get(b, 0.0) for b in bases))
    dedup = float(sum(oews.get(b, 0.0) for b in counts))
    return {
        "frame_occupations": len(frame),
        "distinct_soc_bases": len(counts),
        "bases_with_multiple_onet_codes": len(multi),
        "onet_codes_per_shared_base": multi,
        "employment_sum_with_4_2_join": joined,
        "employment_sum_if_base_counted_once": dedup,
        "join_inflation_factor": round(joined / dedup, 6) if dedup else None,
        "note": ("section 4.2 specifies truncating to the SOC six-digit base "
                 "and joining on OCC_CODE, so each O*NET-SOC code sharing a "
                 "base receives that base's full TOT_EMP; these figures "
                 "quantify the multiplicity rather than silently rescaling it"),
    }


def build_market_profile(occ: pd.DataFrame, tech: pd.DataFrame,
                         skills_im: pd.DataFrame | None,
                         oews: dict[str, float], *, variant: str,
                         tech_soc: list[str]) -> tuple[MarketProfile, dict]:
    """Build one section 4 / 4.5 variant of the O*NET+OEWS market profile.

    Returns (profile, accounting) where accounting holds everything section 6.5
    requires: frame size, dropped codes, normalization statistics.
    """
    assert variant in VARIANT_ORDER, variant

    strings_field = "commodity" if variant == "commodity-title" else "example"
    weighting = ("importance" if variant == "importance-weighted"
                 else "one" if variant == "unweighted" else "employment")
    occ_subset = tech_soc if variant == "computing-IT" else None

    prof = MarketProfile(
        variant, "Commodity Title" if strings_field == "commodity"
        else "Example (fallback Commodity Title)")

    # ---- frame (4.1): distinct O*NET-SOC with >=1 Technology Skills row ----
    occ_codes = list(dict.fromkeys(occ["O*NET-SOC Code"].astype(str)))
    if occ_subset is not None:
        want = set(occ_subset)
        occ_codes = [c for c in occ_codes if soc_base(c) in want]
    with_tech = set(tech["O*NET-SOC Code"].astype(str))

    frame: list[str] = []
    dropped_no_oews: list[str] = []
    for c in occ_codes:
        if c not in with_tech:
            continue                                   # 4.1: needs >=1 tech row
        if soc_base(c) in oews and np.isfinite(oews[soc_base(c)]):
            frame.append(c)
        else:
            dropped_no_oews.append(c)                  # 4.2: reported, not zeroed

    frame = sorted(frame)                              # deterministic ordering
    frame_set = set(frame)

    # ---- per-occupation skill sets (4.3, 4.5) ----
    if variant == "importance-weighted":
        # 4.5 variant 4: the vocabulary is O*NET *skill statements* from
        # Skills.txt (Scale ID IM), not technology tool names, and the IM value
        # is multiplied into w(o).  Appendix table only, because -- as the
        # preregistration says -- its vocabulary is statements, not tool names.
        if skills_im is None or not len(skills_im):
            raise SystemExit("FATAL: importance-weighted variant needs Skills.txt")
        t = skills_im[skills_im["_occ"].isin(frame_set)].copy()
        n_before = len(t)
        t = t[t["_skill"] != ""]
        t = t.assign(_imp=pd.to_numeric(t["_val"],
                                        errors="coerce").fillna(0.0))
        prof.example_empty = 0
        prof.commodity_fallback = 0
        prof.string_field = "Skills.txt Element Name (Scale ID IM)"
    else:
        t = tech.assign(_occ=tech["O*NET-SOC Code"].astype(str))
        t = t[t["_occ"].isin(frame_set)]
        n_before = len(t)

        ex = t["Example"].map(normalize)
        cm = t["Commodity Title"].map(normalize)
        empty_ex = (ex == "").to_numpy()
        nonempty_cm = cm.to_numpy() != ""
        prof.example_empty = int(empty_ex.sum())
        prof.commodity_fallback = int((empty_ex & nonempty_cm).sum())
        if variant == "commodity-title":
            # 4.5 variant 1: Commodity Title *instead of* Example
            chosen = cm.to_numpy()
        else:
            # 4.3: Example with fallback to Commodity Title
            chosen = np.where(empty_ex, cm.to_numpy(), ex.to_numpy())
        t = t.assign(_skill=chosen)
        t = t[t["_skill"] != ""]
        t = t.assign(_imp=1.0)

    # dedup on (occupation, normalized skill), first occurrence wins (4.3)
    t = t.drop_duplicates(subset=["_occ", "_skill"], keep="first")
    n_after = len(t)
    prof.n_before_dedup = n_before
    prof.n_after_dedup = n_after

    by_occ: dict[str, list[tuple[str, float]]] = {c: [] for c in frame}
    for c, s, imp in zip(t["_occ"], t["_skill"], t["_imp"]):
        by_occ[c].append((s, float(imp)))

    # ---- frame occupations and their skill index/weight arrays ----
    for i, c in enumerate(frame):
        base_w = 1.0 if weighting == "one" else float(oews[soc_base(c)])
        pairs = by_occ.get(c) or []
        if not pairs:
            continue
        idxs: list[int] = []
        wts: list[float] = []
        for s, imp in pairs:
            j = prof.vocab.get(s)
            if j is None:
                j = len(prof.vocab_list)
                prof.vocab[s] = j
                prof.vocab_list.append(s)
            idxs.append(j)
            wts.append(base_w * imp)
        prof.occ_codes.append(c)
        prof.sk_idx.append(np.asarray(idxs, np.int64))
        prof.sk_wt.append(np.asarray(wts, np.float64))

    prof.w = np.array(
        [1.0 if weighting == "one" else float(oews[soc_base(c)])
         for c in prof.occ_codes], dtype=np.float64)

    acct = {
        "variant": variant,
        "string_field": prof.string_field,
        "weighting": weighting,
        "frame_size": prof.n_occ,
        "frame_size_before_profile_source_filter": len(frame),
        "frame_occupations_without_profile_rows": len(frame) - prof.n_occ,
        "frame_dropped_no_oews_count": len(dropped_no_oews),
        "frame_dropped_no_oews_codes": dropped_no_oews,
        "frame_dropped_no_tech_row": (len(occ_codes) - len(frame)
                                      - len(dropped_no_oews)),
        "tech_rows_matched_to_frame": int(n_before),
        "tech_rows_after_dedup": int(n_after),
        "tech_rows_removed_by_dedup": int(n_before - n_after),
        "example_empty_rows": prof.example_empty,
        "commodity_title_fallback_rows": prof.commodity_fallback,
        "vocabulary_size": len(prof.vocab_list),
        "weight_total": float(prof.w.sum()),
        "employment_multiplicity": employment_multiplicity(frame, oews),
        "employment_note": ("shares are reported at occupation level "
                            "sum_o w(o) and at skill level sum_s D(s), "
                            "labelled distinctly (4.4)"),
    }
    if variant == "computing-IT":
        want = set(tech_soc)
        resolved = sorted({soc_base(c) for c in prof.occ_codes})
        acct["tech_soc_crosswalk"] = {
            "requested_codes": sorted(want),
            "requested_count": len(want),
            "resolved_bases": resolved,
            "resolved_count": len(resolved),
            "unresolved_bases": sorted(want - set(resolved)),
            "onet_soc_codes_matched": prof.occ_codes,
            "onet_soc_code_count": len(prof.occ_codes),
            "note": ("ALIGN05_PREREG section 4 freezes 16 SOC 2018 detailed "
                     "codes and requires the crosswalk to be re-verified "
                     "against the recorded O*NET-SOC release at run time; "
                     "several codes are absent from O*NET 30.0 entirely, and "
                     "some resolved bases carry more than one O*NET-SOC code "
                     "(e.g. .00 and .01), which is why 16 bases yield more "
                     "than 16 frame occupations"),
        }
    return prof, acct


def demand_weights(prof: MarketProfile, draw: np.ndarray) -> np.ndarray:
    """D(s) = sum_{o : s in Tech(o)} w(o) over the drawn occupations (4.4)."""
    if len(draw) == 0:
        return np.zeros(len(prof.vocab_list), np.float64)
    idx_parts = [prof.sk_idx[i] for i in draw]
    wt_parts = [prof.sk_wt[i] for i in draw]
    return np.bincount(np.concatenate(idx_parts),
                       weights=np.concatenate(wt_parts),
                       minlength=len(prof.vocab_list)).astype(np.float64)


def order_top(d: np.ndarray, vocab: list[str], k: int) -> list[int]:
    """Descending demand weight, ties by ascending normalized string (4.3).

    Partition first so a full sort only ever sees the k candidates.
    """
    nz = np.flatnonzero(d > 0)
    if len(nz) == 0:
        return []
    if len(nz) <= k:
        sel = nz
    else:
        kth = np.partition(d[nz], -k)[-k]
        sel = nz[d[nz] >= kth]
    return sorted(sel.tolist(), key=lambda i: (-d[i], vocab[i]))[:k]


# ---------------------------------------------------------------------------
# Embedding (disk-cached so section 6.5 wall-clock stays sane)
# ---------------------------------------------------------------------------

def get_model():
    global _MODEL
    if _MODEL is None:
        import torch
        from sentence_transformers import SentenceTransformer
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _MODEL = SentenceTransformer(MODEL_NAME, device=device)
        log(f"  embedding model {MODEL_NAME} on {device}")
    return _MODEL


def embed(strings: list[str], tag: str) -> np.ndarray:
    """L2-normalised embeddings, cached under datasets/onet/emb_cache/."""
    EMB_CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(
        (MODEL_NAME + "\0" + "\n".join(strings)).encode("utf-8")).hexdigest()[:16]
    path = EMB_CACHE / f"{tag}_{key}.npy"
    if path.is_file():
        arr = np.load(path)
        if arr.ndim == 2 and arr.shape[0] == len(strings):
            return arr
    arr = get_model().encode(strings, show_progress_bar=False,
                             convert_to_numpy=True, batch_size=256)
    arr = arr / np.linalg.norm(arr, axis=1, keepdims=True)
    np.save(path, arr)
    return arr


# ---------------------------------------------------------------------------
# Import the instrument (2.2: imported, never rewritten)
# ---------------------------------------------------------------------------

def load_instruments() -> None:
    global SENS01, ALIGN03
    if SENS01 is None:
        SENS01 = _import_path("align06_sens01", SENS01_PATH)
    if ALIGN03 is None:
        ALIGN03 = _import_path("align06_align03", ALIGN03_PATH)
    log(f"  SENS01  PROFILE_N={SENS01.PROFILE_N} K_GRID={SENS01.K_GRID} "
        f"MODEL={SENS01.MODEL_NAME} SEED={SENS01.SEED}")
    log(f"  ALIGN03 categories={len(ALIGN03.SKILL_CATEGORIES)} "
        f"SEED={ALIGN03.SEED} BOOTSTRAP_N={ALIGN03.BOOTSTRAP_N}")


# ---------------------------------------------------------------------------
# Section 6.1 control gate (blocking)
# ---------------------------------------------------------------------------

def check_control() -> dict:
    if not CONTROL_JSON.is_file():
        raise SystemExit(
            "FATAL: section 6.1 control has not been run.\n"
            "       Run `python experiments/align06_control.py` first; the\n"
            "       preregistration forbids reporting any O*NET cell until\n"
            "       the 0.52 / 0.32 anchors reproduce.")
    data = json.loads(CONTROL_JSON.read_text(encoding="utf-8"))
    if data.get("status") != "passed":
        raise SystemExit(
            "FATAL: section 6.1 control FAILED; the preregistration makes this\n"
            "       blocking, so no O*NET cell may be written.")
    log(f"  section 6.1 control: PASSED ({data.get('runtime_sec')}s)")
    return data


# ---------------------------------------------------------------------------
# Coverage helpers -- both reproduce the SENS01 rules exactly
# ---------------------------------------------------------------------------

def lexical_coverage(mkt_top, acd_top, mkt_vocab, acd_vocab,
                     k: int) -> tuple[float, np.ndarray]:
    """Symmetric top-k vs top-k intersection on strings (SENS01's rule).

    Section 5 defines the comparison as symmetric, so when one side's profile
    is shorter than K (the importance-weighted variant holds only 35 skill
    statements) both sides are truncated to the same effective k.
    """
    kk = min(k, len(mkt_top), len(acd_top))
    acd_set = {acd_vocab[i] for i in acd_top[:kk]}
    mkt = [mkt_vocab[i] for i in mkt_top[:kk]]
    if not mkt:
        return 0.0, np.zeros(0, np.float64)
    ind = np.fromiter((1.0 if s in acd_set else 0.0 for s in mkt),
                      dtype=np.float64, count=len(mkt))
    return float(ind.mean()), ind


def semantic_matrix(mkt_top, acd_top, mkt_emb, acd_emb) -> np.ndarray:
    """S = M @ A.T over L2-normalised rows (SENS01 section 2 rule)."""
    mi = np.asarray(mkt_top, np.int64)
    ai = np.asarray(acd_top, np.int64)
    if mi.size == 0 or ai.size == 0:
        return np.zeros((mi.size, ai.size), np.float64)
    return mkt_emb[mi] @ acd_emb[ai].T


def semantic_coverage(S: np.ndarray, k: int,
                      tau: float) -> tuple[float, np.ndarray]:
    """maxs = S[:k,:k].max(axis=1); coverage = mean(maxs >= tau)."""
    if S.shape[0] == 0 or S.shape[1] == 0:
        return 0.0, np.zeros(0, np.float64)
    kk = min(k, S.shape[0], S.shape[1])
    maxs = S[:kk, :kk].max(axis=1)
    ind = (maxs >= tau).astype(np.float64)
    return float(ind.mean()), ind


def ci_skill(ind: np.ndarray) -> tuple[float, float]:
    """Resample of the K coverage indicators, B=1000, seed 42 (section 5)."""
    if ind.size == 0:
        return float("nan"), float("nan")
    rng = np.random.RandomState(SEED)
    n = ind.size
    idx = rng.randint(0, n, size=(B_SKILL, n))
    sgi = 1.0 - ind[idx].mean(axis=1)
    return (float(np.percentile(sgi, 2.5)),
            float(np.percentile(sgi, 97.5)))


def resampled_academic_counts(acad, rows: np.ndarray) -> np.ndarray:
    """Counts over academic vocab after resampling the 1,167 rows (section 5)."""
    flat, offs = acad.flat, acad.offsets
    n_vocab = len(acad.vocab_list)
    uniq, mult = np.unique(rows, return_counts=True)
    parts = [flat[offs[r]:offs[r + 1]] for r in uniq]
    lens = [len(p) for p in parts]
    if not any(lens):
        return np.zeros(n_vocab, np.float64)
    return np.bincount(np.concatenate(parts),
                       weights=np.repeat(mult.astype(np.float64), lens),
                       minlength=n_vocab).astype(np.float64)


def academic_top(acad, counts: np.ndarray) -> np.ndarray:
    return SENS01.top_profile(counts, backing=PROFILE_N)


# ---------------------------------------------------------------------------
# Grid (sections 5 + 6.2)
# ---------------------------------------------------------------------------

def build_all_variants(occ, tech, skills_im, oews) -> tuple[dict, dict]:
    variants, accounting = {}, {}
    for v in VARIANT_ORDER:
        t = time.time()
        prof, acct = build_market_profile(
            occ, tech, skills_im, oews, variant=v, tech_soc=TECH_SOC)
        acct["build_sec"] = round(time.time() - t, 2)
        variants[v] = prof
        accounting[v] = acct
        log(f"  variant {v:<20} frame={prof.n_occ:>5} "
            f"vocab={len(prof.vocab_list):>6} "
            f"dropped_no_oews={acct['frame_dropped_no_oews_count']:>4} "
            f"dedup_removed={acct['tech_rows_removed_by_dedup']:>5} "
            f"({acct['build_sec']}s)")
    return variants, accounting


def draw_for(prof: MarketProfile, p) -> tuple[np.ndarray, int, bool]:
    """One seeded SRS without replacement from the sorted frame (section 5).

    seed = 42 + 10 * P_index.  When P exceeds the frame size -- the computing/IT
    stratum holds 16 occupations, so every P in the grid exceeds it -- the draw
    is the whole frame.  The cap is returned explicitly so it reaches
    metrics.json instead of being implicit.
    """
    n = prof.n_occ
    if p == "all":
        return np.arange(n, dtype=np.int64), n, False
    p_index = P_GRID.index(p)
    take = min(p, n)
    rng = np.random.RandomState(SEED + 10 * p_index)
    draw = rng.choice(n, size=take, replace=False)
    return np.sort(draw.astype(np.int64)), take, take < p


def make_row(*, variant, match, tau, k, p, sgi, cov, ind, prof, drawn, capped,
             prof_n, acd_n, eff_n) -> dict:
    lo, hi = ci_skill(ind)
    return {
        "variant": variant, "match": match, "tau": tau, "K": k, "P": p,
        "SGI": round(float(sgi), 6), "coverage": round(float(cov), 6),
        "CI_skill_lower": round(lo, 6), "CI_skill_upper": round(hi, 6),
        "CI_occ_lower": "", "CI_occ_upper": "",
        "frame_size": prof.n_occ, "draw_size": drawn,
        "market_profile_n": prof_n, "academic_profile_n": acd_n,
        "effective_profile_n": eff_n,
        "p_capped_to_frame": bool(capped),
    }


def run_grid(variants: dict, acad, control: dict) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    acad_vocab = acad.vocab_list
    acd_top_fixed = academic_top(acad, SENS01.full_counts(acad))
    acd_emb = embed(acad_vocab, "acad")

    emb_cache: dict[str, np.ndarray] = {}
    occ_boot: dict[tuple[str, object], dict] = {}

    for vname, prof in variants.items():
        vocab = prof.vocab_list
        log(f"\n-- variant {vname} (vocab {len(vocab)}, frame {prof.n_occ}) --")
        mkt_emb = embed(vocab, f"mkt_{vname}")
        emb_cache[vname] = mkt_emb

        for p in P_GRID + ["all"]:
            t = time.time()
            draw, drawn, capped = draw_for(prof, p)
            d = demand_weights(prof, draw)
            mkt_top = order_top(d, vocab, PROFILE_N)
            # one matrix per cell-set: reused across every K and tau
            S = semantic_matrix(mkt_top, acd_top_fixed, mkt_emb, acd_emb)

            for k in K_GRID:
                # both sides truncated to the same k (section 5, symmetric)
                kk = min(k, len(mkt_top), len(acd_top_fixed))
                mk = min(k, len(mkt_top))
                ak = min(k, len(acd_top_fixed))

                cov, ind = lexical_coverage(mkt_top, acd_top_fixed,
                                            vocab, acad_vocab, k)
                rows.append(make_row(variant=vname, match="lexical", tau="",
                                     k=k, p=p, sgi=1.0 - cov, cov=cov, ind=ind,
                                     prof=prof, drawn=drawn, capped=capped,
                                     prof_n=mk, acd_n=ak, eff_n=kk))

                for tau in TAUS:
                    cov, ind = semantic_coverage(S, k, tau)
                    rows.append(make_row(variant=vname, match="semantic",
                                         tau=tau, k=k, p=p, sgi=1.0 - cov,
                                         cov=cov, ind=ind, prof=prof,
                                         drawn=drawn, capped=capped,
                                         prof_n=mk, acd_n=ak, eff_n=kk))
            log(f"  P={str(p):<4} drawn={drawn:<5} profile={len(mkt_top):<4} "
                f"{time.time() - t:.1f}s")

        for p in P_GRID:
            t = time.time()
            log(f"  CI_occ bootstrap {vname} / P={p} (B={B_OCC}) ...",
                )
            occ_boot[(vname, p)] = ci_occ(prof=prof, p=p, acad=acad,
                                          vocab=vocab, mkt_emb=mkt_emb,
                                          acd_emb=acd_emb)
            log(f"    done in {time.time() - t:.1f}s")

    # ---- attach CI_occ (NaN at P = all, exactly as CI_post is in SENS01) ----
    for r in rows:
        if r["P"] == "all":
            continue
        b = occ_boot.get((r["variant"], r["P"]))
        if b is None:
            continue
        if r["match"] == "lexical":
            arr = b["lex"][:, K_GRID.index(r["K"])]
        else:
            arr = b["sem"][:, K_GRID.index(r["K"]), TAUS.index(r["tau"])]
        r["CI_occ_lower"] = round(float(np.percentile(arr, 2.5)), 6)
        r["CI_occ_upper"] = round(float(np.percentile(arr, 97.5)), 6)

    return rows, occ_boot


def ci_occ(*, prof: MarketProfile, p, acad, vocab: list[str],
           mkt_emb: np.ndarray, acd_emb: np.ndarray) -> dict:
    """Section 5: resample the P occupations AND all 1,167 academic rows,
    rebuilding the O*NET top-K profile per replicate.  B=500, seed 42."""
    n = prof.n_occ
    take = n if p == "all" else min(p, n)
    acd_vocab = acad.vocab_list
    n_acad_rows = len(acad.offsets) - 1

    lex = np.empty((B_OCC, len(K_GRID)), np.float64)
    sem = np.empty((B_OCC, len(K_GRID), len(TAUS)), np.float64)

    rng_occ = np.random.RandomState(SEED)
    rng_acad = np.random.RandomState(SEED)

    for b in range(B_OCC):
        draw = rng_occ.choice(n, size=take, replace=True)
        mkt_top = order_top(demand_weights(prof, draw), vocab, PROFILE_N)

        rows = rng_acad.randint(0, n_acad_rows, size=n_acad_rows)
        acd_top = academic_top(acad, resampled_academic_counts(acad, rows))

        for ki, k in enumerate(K_GRID):
            cov, ind = lexical_coverage(mkt_top, acd_top, vocab, acd_vocab, k)
            lex[b, ki] = 1.0 - cov

        S = semantic_matrix(mkt_top, acd_top, mkt_emb, acd_emb)
        for ki, k in enumerate(K_GRID):
            for ti, tau in enumerate(TAUS):
                cov, _ = semantic_coverage(S, k, tau)
                sem[b, ki, ti] = 1.0 - cov
    return {"lex": lex, "sem": sem}


# ---------------------------------------------------------------------------
# 6.3 taxonomy category report
# ---------------------------------------------------------------------------

def run_category_report(variants: dict, acad) -> list[dict]:
    exclusive = ALIGN03.exclusive_taxonomy()
    categories = list(exclusive.keys())
    n_cats = len(categories)

    tax_skills: list[str] = []
    tax_cat: list[int] = []
    for ci, cat in enumerate(categories):
        for s in exclusive[cat]:
            tax_skills.append(s)
            tax_cat.append(ci)
    n_tax = len(tax_skills)
    tax_index = {s: i for i, s in enumerate(tax_skills)}
    tax_cat_arr = np.asarray(tax_cat, np.int64)
    tax_emb = embed(tax_skills, "taxonomy")

    prof = variants["economy-wide"]
    vocab = prof.vocab_list
    n = prof.n_occ
    w = prof.w

    # per-occupation (occupation, taxonomy-skill, category) triples -- computed
    # once because neither the frame nor the taxonomy depends on K or tau.
    occ_arr: list[int] = []
    tax_pos: list[int] = []
    cat_id: list[int] = []
    den = np.zeros((n, n_cats), np.float64)
    present = np.zeros((n, n_cats), np.float64)
    for i in range(n):
        seen: set[int] = set()
        for j in prof.sk_idx[i]:
            ti = tax_index.get(vocab[j])
            if ti is None:
                continue
            occ_arr.append(i)
            tax_pos.append(ti)
            cat_id.append(tax_cat[ti])
            den[i, tax_cat[ti]] += 1.0
            seen.add(tax_cat[ti])
        for c in seen:
            present[i, c] = 1.0
    occ_arr_a = np.asarray(occ_arr, np.int64)
    tax_pos_a = np.asarray(tax_pos, np.int64)
    cat_id_a = np.asarray(cat_id, np.int64)
    log(f"  taxonomy skills={n_tax} across {n_cats} categories; "
        f"occupation-skill pairs in taxonomy={len(occ_arr)}")

    def cov_matrix(flag: np.ndarray) -> np.ndarray:
        """flag is boolean over tax_skills -> (n_occ, n_cats) coverage counts."""
        m = flag[tax_pos_a]
        if not m.any():
            return np.zeros((n, n_cats), np.float64)
        flat = cat_id_a[m] * n + occ_arr_a[m]
        return np.bincount(flat, minlength=n * n_cats
                           ).reshape(n, n_cats).astype(np.float64)

    def rates(cov: np.ndarray, occ_idx: np.ndarray, w_b: np.ndarray,
              den_b: np.ndarray, demand_b: np.ndarray) -> tuple[np.ndarray,
                                                                np.ndarray]:
        cov_b = (cov[occ_idx] * w_b[:, None]).sum(axis=0)
        rate = np.where(den_b > 0, cov_b / np.maximum(den_b, 1e-12), 0.0)
        return rate, demand_b * (1.0 - rate)

    def demand_of(occ_idx: np.ndarray, w_b: np.ndarray) -> np.ndarray:
        return 100.0 * (present[occ_idx] * w_b[:, None]).sum(axis=0) / w_b.sum()

    acd_vocab = acad.vocab_list
    acd_emb = embed(acd_vocab, "acad")
    acd_top_fixed = academic_top(acad, SENS01.full_counts(acad))
    flat, offs = acad.flat, acad.offsets
    n_acad_rows = len(acad.offsets) - 1

    all_idx = np.arange(n, dtype=np.int64)

    def build_flags(acd_top) -> tuple[dict, np.ndarray]:
        """lexical flag per K + semantic max-similarity matrix (n_tax, 500)."""
        acd_rows = acd_emb[np.asarray(acd_top, np.int64)]
        sims = tax_emb @ acd_rows.T
        lex = {}
        for k in K_GRID:
            top_k = {acd_vocab[i] for i in acd_top[:k]}
            lex[k] = np.fromiter((s in top_k for s in tax_skills),
                                 dtype=bool, count=n_tax)
        return lex, sims

    rows: list[dict] = []

    # ---- point estimate: fixed academic profile, whole frame ----
    lex_flags, sims = build_flags(acd_top_fixed)
    demand_pt = demand_of(all_idx, w)
    den_pt = (den * w[:, None]).sum(axis=0)
    for k in K_GRID:
        rate, deficit = rates(cov_matrix(lex_flags[k]), all_idx, w,
                              den_pt, demand_pt)
        rows.extend(_cat_rows(categories, demand_pt, rate, deficit,
                              "lexical", k, ""))
        maxs = sims[:, :k].max(axis=1)
        for tau in TAUS:
            rate, deficit = rates(cov_matrix(maxs >= tau), all_idx, w,
                                  den_pt, demand_pt)
            rows.extend(_cat_rows(categories, demand_pt, rate, deficit,
                                  "semantic", k, tau))

    # ---- CI_occ bootstrap, B = 1000, seed 42 (6.3) ----
    log(f"  category CI_occ bootstrap (B={B_OCC_CAT}) ...")
    dem_b = np.zeros((B_OCC_CAT, n_cats), np.float64)
    rate_lex_b = np.zeros((B_OCC_CAT, n_cats, len(K_GRID)), np.float64)
    def_lex_b = np.zeros((B_OCC_CAT, n_cats, len(K_GRID)), np.float64)
    rate_sem_b = np.zeros((B_OCC_CAT, n_cats, len(K_GRID), len(TAUS)),
                          np.float64)
    def_sem_b = np.zeros((B_OCC_CAT, n_cats, len(K_GRID), len(TAUS)),
                         np.float64)

    rng_occ = np.random.RandomState(SEED)
    rng_acad = np.random.RandomState(SEED)
    t = time.time()
    for b in range(B_OCC_CAT):
        rows_b = rng_acad.randint(0, n_acad_rows, size=n_acad_rows)
        acd_top_b = academic_top(acad, resampled_academic_counts(acad, rows_b))
        lex_flags, sims = build_flags(acd_top_b)

        occ_idx = rng_occ.randint(0, n, size=n)
        w_b = w[occ_idx]
        den_b = (den[occ_idx] * w_b[:, None]).sum(axis=0)
        demand_b = demand_of(occ_idx, w_b)
        dem_b[b] = demand_b

        for ki, k in enumerate(K_GRID):
            rate, deficit = rates(cov_matrix(lex_flags[k]), occ_idx, w_b,
                                  den_b, demand_b)
            rate_lex_b[b, :, ki] = rate
            def_lex_b[b, :, ki] = deficit
            maxs = sims[:, :k].max(axis=1)
            for ti, tau in enumerate(TAUS):
                rate, deficit = rates(cov_matrix(maxs >= tau), occ_idx, w_b,
                                      den_b, demand_b)
                rate_sem_b[b, :, ki, ti] = rate
                def_sem_b[b, :, ki, ti] = deficit
        if (b + 1) % 200 == 0:
            log(f"    {b + 1}/{B_OCC_CAT}  ({time.time() - t:.0f}s)")

    # ---- attach CIs ----
    for r in rows:
        ki = K_GRID.index(r["K"])
        r["CI_demand_lower"] = round(
            float(np.percentile(dem_b[:, categories.index(r["category"])], 2.5)), 4)
        r["CI_demand_upper"] = round(
            float(np.percentile(dem_b[:, categories.index(r["category"])], 97.5)), 4)
        ci = categories.index(r["category"])
        if r["match"] == "lexical":
            arr_d = def_lex_b[:, ci, ki]
            arr_r = rate_lex_b[:, ci, ki]
        else:
            ti = TAUS.index(r["tau"])
            arr_d = def_sem_b[:, ci, ki, ti]
            arr_r = rate_sem_b[:, ci, ki, ti]
        r["CI_deficit_lower"] = round(float(np.percentile(arr_d, 2.5)), 4)
        r["CI_deficit_upper"] = round(float(np.percentile(arr_d, 97.5)), 4)
        r["CI_rate_lower"] = round(float(np.percentile(arr_r, 2.5)), 6)
        r["CI_rate_upper"] = round(float(np.percentile(arr_r, 97.5)), 6)
    log(f"  category bootstrap done in {time.time() - t:.0f}s")
    return rows


def _cat_rows(categories, demand, rate, deficit, match, k, tau) -> list[dict]:
    out = []
    for ci, cat in enumerate(categories):
        out.append({
            "category": cat, "match": match, "K": k, "tau": tau,
            "market_demand_pp": round(float(demand[ci]), 4),
            "coverage_rate": round(float(rate[ci]), 6),
            "deficit_pp": round(float(deficit[ci]), 4),
            "CI_demand_lower": "", "CI_demand_upper": "",
            "CI_rate_lower": "", "CI_rate_upper": "",
            "CI_deficit_lower": "", "CI_deficit_upper": "",
        })
    return out


# ---------------------------------------------------------------------------
# 6.4 descriptive cross-source comparison (never used to select parameters)
# ---------------------------------------------------------------------------

def run_cross_source(variants: dict) -> list[dict]:
    from scipy.stats import spearmanr

    prof = variants["economy-wide"]
    vocab = prof.vocab_list
    d = demand_weights(prof, np.arange(prof.n_occ, dtype=np.int64))
    onet_map = {vocab[i]: float(d[i]) for i in np.flatnonzero(d)}
    onet_top = order_top(d, vocab, PROFILE_N)

    def token_weights(ti):
        counts = SENS01.full_counts(ti)
        top = SENS01.top_profile(counts, backing=PROFILE_N)
        vt = ti.vocab_list
        return [vt[i] for i in top], {vt[i]: float(counts[i]) for i in top}

    sources: dict[str, tuple[list[str], dict]] = {}
    log("  loading HF postings corpus ...")
    sources["HF postings (ALIGN01/02 market side)"] = token_weights(
        SENS01.load_market_hf())
    try:
        log("  loading LinkedIn 1.3M corpus ...")
        sources["LinkedIn 1.3M scrape (ALIGN04)"] = token_weights(
            SENS01.load_market_linkedin())
    except Exception as exc:                       # artifact absent -> skip
        log(f"  LinkedIn corpus unavailable ({type(exc).__name__}: {exc}); "
            f"recording it as absent rather than substituting a source")

    rows: list[dict] = []
    for name, (other_top, other_map) in sources.items():
        for k in K_GRID:
            a = [vocab[i] for i in onet_top[:k]]
            b = other_top[:k]
            sa, sb = set(a), set(b)
            union = sorted(sa | sb)
            if len(union) > 1:
                ra = np.array([onet_map.get(s, 0.0) for s in union])
                rb = np.array([other_map.get(s, 0.0) for s in union])
                rho = float(spearmanr(ra, rb).statistic)
            else:
                rho = float("nan")
            inter = len(sa & sb)
            rows.append({
                "other_source": name, "K": k,
                "jaccard_topK": round(inter / len(union), 6) if union else 0.0,
                "spearman_rho_weight_vectors": round(rho, 6),
                "intersection": inter, "union": len(union),
                "interpretation": "descriptive only; cannot select parameters",
            })
    return rows


# ---------------------------------------------------------------------------
# 6.5 metrics.json + artifacts
# ---------------------------------------------------------------------------

def write_outputs(grid_rows, cat_rows, cross_rows, accounting, variants,
                  control, acad, oews_prov, onet_prov, elapsed) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(grid_rows).to_csv(OUT_DIR / "table_sgi_onet_grid.csv",
                                   index=False)
    pd.DataFrame(cat_rows).to_csv(OUT_DIR / "table_category_gap_onet.csv",
                                  index=False)
    pd.DataFrame(cross_rows).to_csv(OUT_DIR / "table_cross_source.csv",
                                    index=False)

    # ---- 6.2: top profile table ----
    prof = variants["economy-wide"]
    vocab = prof.vocab_list
    d = demand_weights(prof, np.arange(prof.n_occ, dtype=np.int64))
    top = order_top(d, vocab, PROFILE_N)
    dsum = float(d.sum())
    wsum = float(prof.w.sum())
    tbl = [{
        "rank": r, "skill": vocab[i],
        "demand_weight_D_s": round(float(d[i]), 4),
        "demand_share_skill_level": round(float(d[i]) / dsum, 8) if dsum else "",
        "demand_share_occupation_level": round(float(d[i]) / wsum, 8) if wsum else "",
    } for r, i in enumerate(top, start=1)]
    pd.DataFrame(tbl).to_csv(OUT_DIR / "table_onet_profile_top.csv", index=False)

    # ---- 7.3 registered contrasts ----
    g = pd.DataFrame(grid_rows)

    def cell(match, k, tau, p="all", variant="economy-wide"):
        q = g[(g["variant"] == variant) & (g["match"] == match)
              & (g["K"] == k) & (g["P"].astype(str) == str(p))]
        if tau != "":
            q = q[q["tau"] == tau]
        return q.iloc[0].to_dict() if len(q) else {}

    a = cell("lexical", 100, "")
    b = cell("semantic", 100, 0.5)
    persist = bool(b) and float(b.get("CI_skill_lower") or 0) > 0

    metrics = {
        "experiment_id": "ALIGN06_onet_demand_profile",
        "status": "completed",
        "prereg": "experiments/ALIGN06_PREREG.md",
        "completed_utc": now_utc(),
        "wall_clock_sec": round(elapsed, 3),
        "seed": SEED,
        "seeds": {
            "occupation_draw": "42 + 10 * P_index (section 5)",
            "CI_skill": SEED, "CI_occ": SEED, "category_bootstrap": SEED,
        },
        "grid": {"K": K_GRID, "P": P_GRID + ["all"], "tau": TAUS,
                 "match": ["lexical", "semantic"], "stratum": VARIANT_ORDER},
        "bootstrap": {"B_SKILL": B_SKILL, "B_OCC": B_OCC,
                      "B_OCC_category": B_OCC_CAT},
        "control_6_1": {
            "status": control.get("status"),
            "runtime_sec": control.get("runtime_sec"),
            "lexical_K100_P_all": control.get("cells", {}).get(
                "lexical_K100_P_all", {}),
            "semantic_K100_tau0.5_P_all": control.get("cells", {}).get(
                "semantic_K100_tau0.5_P_all", {}),
        },
        "sources": {
            "onet": onet_prov, "oews": oews_prov,
            "license_snapshots": [
                str((LIC_SNAPSHOT_DIR / "onet_db_30_0.txt").relative_to(ROOT)),
                str((LIC_SNAPSHOT_DIR / "bls_oes_m2025.txt").relative_to(ROOT)),
            ],
            "license_note": ("O*NET 30.0 Database is CC BY 4.0 (attribution "
                             "required); BLS OEWS is public domain with source "
                             "citation requested; the BLS emblem is a "
                             "registered trademark and is not used."),
            "attribution": (
                "This analysis uses information from the O*NET 30.0 Database "
                "by the U.S. Department of Labor, Employment and Training "
                "Administration (USDOL/ETA). Used under the CC BY 4.0 license. "
                "O*NET(R) is a trademark of USDOL/ETA. Source: U.S. Bureau of "
                "Labor Statistics, Occupational Employment and Wage "
                "Statistics (OEWS), May 2025 national estimates."),
        },
        "frame": accounting,
        "stratum_sizes": {v: variants[v].n_occ for v in VARIANT_ORDER},
        "normalization": {
            "rule": ("Unicode NFKC -> casefold -> collapse internal whitespace "
                     "-> strip surrounding punctuation and trademark markers "
                     "(section 4.3)"),
            "strip_chars": _STRIP_CHARS,
            "strip_chars_note": ("'+ # / - & _' are deliberately NOT stripped: "
                                 "they are part of technology names (c++, c#, "
                                 "f#, node.js). '.' is stripped only at the "
                                 "right; a leading '.' followed by a word "
                                 "character is preserved because the posting "
                                 "corpora spell the framework '.net'."),
            "leading_dot_preserved": True,
            "residual_surrounding_punctuation_rows": 0,
            "dedup_key": "(occupation, normalized skill), first occurrence wins",
        },
        "vocabulary_overlap": _vocab_overlap(variants, acad),
        "registered_contrasts": {
            "a_lexical_economywide_P_all_K100_vs_0.52": a,
            "b_semantic_economywide_P_all_K100_tau0.5_vs_0.32": b,
            "c_persistence_claim_permitted": persist,
            "c_rule": ("permitted only if the CI_skill lower bound of cell (b) "
                       "is > 0 (section 7.3)"),
        },
        "estimand_caveat": (
            "The market side is employment-weighted occupations from a US "
            "expert taxonomy, not posting counts from a global scrape -- equal "
            "SGI levels would be convergence across two different estimands, "
            "and different levels are not by themselves evidence against the "
            "posting-based result (section 7.2). This is a level comparison, "
            "not a replacement: no published headline number is edited from "
            "ALIGN06 (section 7.1)."),
        "counts": {"grid_rows": len(grid_rows), "category_rows": len(cat_rows),
                   "cross_source_rows": len(cross_rows)},
    }
    (OUT_DIR / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    log(f"\nwrote metrics.json, table_sgi_onet_grid.csv ({len(grid_rows)}), "
        f"table_category_gap_onet.csv ({len(cat_rows)}), "
        f"table_onet_profile_top.csv ({len(tbl)}), "
        f"table_cross_source.csv ({len(cross_rows)})")


def _vocab_overlap(variants: dict, acad) -> dict:
    a = set(acad.vocab_list)
    out = {}
    for v, prof in variants.items():
        m = set(prof.vocab_list)
        out[v] = {
            "onet_vocab": len(m), "academic_vocab": len(a),
            "intersection": len(m & a),
            "onet_share_in_academic": round(len(m & a) / len(m), 6) if m else 0.0,
            "academic_share_in_onet": round(len(m & a) / len(a), 6) if a else 0.0,
        }
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def load_onet_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame,
                                dict]:
    readme = ONET_DIR / "Read Me.txt"
    release_txt = (readme.read_text(encoding="utf-8", errors="replace")
                   if readme.is_file() else "")
    if ONET_RELEASE_EXPECTED not in release_txt:
        raise SystemExit(
            f"FATAL: release pin mismatch -- {ONET_RELEASE_EXPECTED} not found "
            f"in {readme}")
    log(f"  release pin OK: {ONET_RELEASE_EXPECTED} present in Read Me.txt")

    occ = pd.read_csv(ONET_DIR / "Occupation Data.txt", sep="\t",
                      dtype=str, keep_default_na=False)
    tech = pd.read_csv(ONET_DIR / "Technology Skills.txt", sep="\t",
                       dtype=str, keep_default_na=False)
    skills = pd.read_csv(ONET_DIR / "Skills.txt", sep="\t",
                         dtype=str, keep_default_na=False)
    log(f"  O*NET: {len(occ)} occupations, {len(tech)} technology rows, "
        f"{len(skills)} skill rows")

    skills_im = None
    if "Scale ID" in skills.columns:
        im = skills[skills["Scale ID"].astype(str).str.strip() == "IM"].copy()
        if len(im):
            im = im.rename(columns={"Data Value": "_val"})
            im["_occ"] = im["O*NET-SOC Code"].astype(str)
            im["_skill"] = im["Element Name"].map(normalize)
            im["_val"] = pd.to_numeric(im["_val"], errors="coerce").fillna(0.0)
            skills_im = im
    log(f"  Skills.txt importance rows (Scale ID IM): "
        f"{0 if skills_im is None else len(skills_im)}")

    prov = {
        "archive": str(ONET_ZIP.relative_to(ROOT)),
        "sha256": sha256_file(ONET_ZIP),
        "bytes": ONET_ZIP.stat().st_size,
        "release_declared": "db_30_0",
        "release_verified": ONET_RELEASE_EXPECTED,
        "tables": {fn: ((ONET_DIR / fn).stat().st_size
                        if (ONET_DIR / fn).is_file() else None)
                   for fn in ["Technology Skills.txt", "Occupation Data.txt",
                              "Skills.txt"]},
    }
    log(f"  O*NET sha256 {prov['sha256'][:16]}... ({prov['bytes']} bytes)")
    return occ, tech, skills_im, prov


def pipeline(occ, tech, skills_im, oews, oews_prov, onet_prov, control,
             *, write: bool, elapsed: float) -> None:
    log("\nsection 4: building every profile variant")
    variants, accounting = build_all_variants(occ, tech, skills_im, oews)

    log("\nloading academic reference profile")
    acad = SENS01.load_academic()
    log(f"  academic rows={acad.n_rows} vocab={len(acad.vocab_list)}")

    log("\nsection 6.2: SGI grid + dual bootstrap")
    grid_rows, _ = run_grid(variants, acad, control)

    log("\nsection 6.3: taxonomy category report")
    cat_rows = run_category_report(variants, acad)

    log("\nsection 6.4: descriptive cross-source comparison")
    cross_rows = run_cross_source(variants)

    if not write:
        log("\nSELFTEST ONLY -- nothing written to results/")
        log(f"  grid_rows={len(grid_rows)} cat_rows={len(cat_rows)} "
            f"cross_rows={len(cross_rows)}")
        return

    write_outputs(grid_rows, cat_rows, cross_rows, accounting, variants,
                  control, acad, oews_prov, onet_prov, elapsed)


def main() -> int:
    selftest = "--selftest" in sys.argv[1:]
    t0 = time.time()
    log("== ALIGN06: O*NET x BLS OEWS employment-weighted demand profile ==")
    log(f"   prereg: experiments/ALIGN06_PREREG.md   seed {SEED}"
        f"{'   SELFTEST' if selftest else ''}")

    control = check_control()

    if not ONET_ZIP.is_file() or not ONET_DIR.is_dir():
        raise SystemExit(
            f"FATAL: O*NET archive/table missing at {ONET_ZIP} / {ONET_DIR}")
    load_instruments()
    occ, tech, skills_im, onet_prov = load_onet_tables()

    if selftest:
        # Synthetic all-present employment weights: exercises every code path
        # (frame construction, crosswalk, grid, both bootstraps, 6.3, 6.4)
        # without the OEWS archive.  Its numbers are NOT preregistration
        # results and nothing is written.
        bases = sorted({soc_base(c) for c in occ["O*NET-SOC Code"].astype(str)})
        oews = {b: float(1000 + i) for i, b in enumerate(bases)}
        oews_prov = {"mode": "selftest-synthetic"}
        log("\nSELFTEST: synthetic OEWS weights, nothing will be written")
        pipeline(occ, tech, skills_im, oews, oews_prov, onet_prov, control,
                 write=False, elapsed=0.0)
        log(f"\nselftest OK in {time.time() - t0:.1f}s")
        return 0

    if not OEWS_ZIP.is_file():
        raise SystemExit(
            f"FATAL: missing {OEWS_ZIP}\n"
            "       The OEWS archive is not downloadable from this host or a\n"
            "       Kaggle kernel (BLS returns HTTP 403). Download\n"
            "       https://www.bls.gov/oes/special-requests/oesm25nat.zip\n"
            "       in a normal browser and place it at the path above.")

    oews_prov = {
        "archive": str(OEWS_ZIP.relative_to(ROOT)),
        "sha256": sha256_file(OEWS_ZIP),
        "bytes": OEWS_ZIP.stat().st_size,
        "retrieval": ("supplied by the author's browser; www.bls.gov returns "
                      "HTTP 403 to this host and to a Kaggle kernel (Akamai "
                      "bot management), so the archive could not be fetched "
                      "programmatically"),
    }
    log(f"  OEWS sha256 {oews_prov['sha256'][:16]}... "
        f"({oews_prov['bytes']} bytes)")
    oews, inner = load_oews(OEWS_ZIP)
    oews_prov.update(inner)
    log(f"  OEWS workbook {inner['inner_workbook']} "
        f"({oews_prov['rows_detailed_matched']} detailed occupations matched, "
        f"{oews_prov['rows_detailed_suppressed']} suppressed)")

    pipeline(occ, tech, skills_im, oews, oews_prov, onet_prov, control,
             write=True, elapsed=time.time() - t0)
    log(f"\nALIGN06 complete in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise SystemExit(f"FATAL: {type(exc).__name__}: {exc}")
