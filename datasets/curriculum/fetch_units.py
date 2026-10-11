"""Phase 1 curriculum fetcher (consolidated).

Downloads the HTML snapshots that ``extract_units.py`` later reads, and appends
one evidence record per attempted URL to ``datasets/curriculum/raw/fetch_evidence.jsonl``
(gitignored, like the snapshots themselves).

Consolidates the two ad-hoc scripts this replaces:
  * ``_fetch_pending.py`` - fetch every MANIFEST row whose status is ``pending``
  * ``_refetch.py``       - same, plus Harvard license/ + syllabus/ sub-pages

Behaviour (unchanged from what produced the current evidence log):
  * Polite: checks robots.txt per host, 1.5 s delay, academic UA, 2 MB cap.
  * Saves ``raw/<unit_id>.html`` (bytes as received) and ``raw/<unit_id>.txt``
    (script/style-stripped text, used only for the license/year heuristics).
  * Classifies license as ``license_ok_cc`` / ``license_fail_arr_or_non_cc`` /
    ``license_unclear`` from regex signals in the page text.
  * Extracts year candidates (bare years + years near revised/published/
    "as taught in" context words) for the material-year check.
  * Never computes skill counts or SGI - that stays in extract_units.py /
    CURR02 so that fetching cannot influence analysis.

Evidence fields per record:
  unit_id, status, http_status, content_type, url, robots_note,
  license_status, license_signals, year_candidates, snapshot_html,
  fetched_utc, text_chars

Usage
-----
    python datasets/curriculum/fetch_units.py                  # all pending rows
    python datasets/curriculum/fetch_units.py --no-harvard-extras
    python datasets/curriculum/fetch_units.py --dry-run        # list targets only

Note: ``--dry-run`` prints the URL plan without any network access.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

try:
    import certifi

    _CA = certifi.where()
except Exception:  # pragma: no cover - certifi present in verified env
    _CA = None

SSL_CTX = ssl.create_default_context(cafile=_CA) if _CA else ssl.create_default_context()
ROOT = Path(__file__).resolve().parents[2]
CURR = ROOT / "datasets" / "curriculum"
RAW = CURR / "raw"
RAW.mkdir(parents=True, exist_ok=True)
EVIDENCE = CURR / "raw" / "fetch_evidence.jsonl"
MANIFEST = CURR / "MANIFEST.csv"
UA = "skill-gap-curriculum-research/1.0 (academic; polite; contact: repo owner via GitHub)"
DELAY_S = 1.5
MAX_BYTES = 2_000_000


class _TextExtractor(HTMLParser):
    """Strip script/style/noscript; concatenate remaining text nodes."""

    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    p = _TextExtractor()
    try:
        p.feed(html)
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", " ".join(p.parts)).strip()


def robots_ok(url: str) -> tuple[bool, str]:
    parts = urlparse(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        req = urllib.request.Request(robots_url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as resp:
            data = resp.read(200_000).decode("utf-8", errors="replace")
        rp.parse(data.splitlines())
        allowed = rp.can_fetch(UA, url)
        return allowed, f"robots checked {robots_url}; allowed={allowed}"
    except Exception as e:
        # No robots or fetch fail: allow but log; license must still be clear
        return True, f"robots unavailable/error ({e}); proceeding only if license clear"


def fetch(url: str) -> tuple[int, str, bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en",
        },
    )
    with urllib.request.urlopen(req, timeout=40, context=SSL_CTX) as resp:
        ct = resp.headers.get("Content-Type", "")
        body = resp.read(MAX_BYTES)
        return resp.status, ct, body


LICENSE_PATTERNS = [
    r"CC BY-NC-SA[^\n]{0,40}",
    r"CC BY-SA[^\n]{0,40}",
    r"CC BY[^\n]{0,40}",
    r"CC0[^\n]{0,40}",
    r"Creative Commons[^\n]{0,80}",
    r"All rights reserved",
    r"not licensed under a Creative Commons",
    r"Attribution-NonCommercial-ShareAlike",
]

YEAR_CONTEXT_RE = (
    r"(?:©|copyright|revised|updated|published|last modified|version|"
    r"spring|fall|summer|winter|as taught in)\D{0,40}(20[12][0-9])"
)


def extract_license_signals(text: str) -> list[str]:
    hits = []
    for pat in LICENSE_PATTERNS:
        for m in re.finditer(pat, text, flags=re.I):
            s = max(0, m.start() - 40)
            e = min(len(text), m.end() + 60)
            hits.append(text[s:e].strip())
            if len(hits) >= 8:
                return hits
    return hits


def extract_year_candidates(text: str) -> dict:
    ctx = [m.group(0)[:140] for m in re.finditer(YEAR_CONTEXT_RE, text, flags=re.I)]
    years = sorted(set(re.findall(r"\b(20[12][0-9])\b", text)))
    return {"context": ctx[:16], "years": years}


def classify_license(text: str, lic: list[str]) -> str:
    cc_ok = any(
        re.search(r"cc by|creative commons|attribution-noncommercial-sharealike", x, re.I)
        for x in lic
    )
    arr_only = (not cc_ok) and any("all rights reserved" in x.lower() for x in lic)
    if arr_only:
        return "license_fail_arr_or_non_cc"
    if cc_ok:
        return "license_ok_cc"
    return "license_unclear"


def extra_urls_for(uid: str, url: str, enabled: bool = True) -> list[tuple[str, str]]:
    """Harvard units also need their license/ and syllabus/ sub-pages.

    CS50 sub-pages 404 for some courses; a failed extra is recorded in the
    evidence log like any other failure and does not affect the main snapshot.
    """
    if not enabled or not uid.startswith("HARV-"):
        return []
    base = url.rstrip("/") + "/"
    return [(f"{uid}__lic", base + "license/"), (f"{uid}__syll", base + "syllabus/")]


def plan_targets(harvard_extras: bool) -> list[tuple[str, str]]:
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    pending = [r for r in rows if r["extraction_status"] == "pending"]
    targets: list[tuple[str, str]] = []
    for r in pending:
        uid = r["unit_id"]
        targets.append((uid, r["source_url"].strip()))
        targets.extend(extra_urls_for(uid, r["source_url"].strip(), harvard_extras))
    return targets


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--no-harvard-extras", action="store_true",
                    help="skip the extra license/ + syllabus/ sub-pages for CS50")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the URL plan and exit without network access")
    args = ap.parse_args()

    targets = plan_targets(harvard_extras=not args.no_harvard_extras)
    print(f"targets={len(targets)}")
    if args.dry_run:
        for fid, url in targets:
            print(f"PLAN {fid} {url}")
        return

    results = []
    n_ok = 0
    for fetch_id, url in targets:
        if not url or not url.startswith("http"):
            results.append({"unit_id": fetch_id, "status": "bad_url", "url": url})
            print(f"BAD  {fetch_id}")
            continue
        # skip pure catalog roots (need a concrete course path)
        path = urlparse(url).path.strip("/")
        if path.count("/") < 1 and "cs50" not in url:
            results.append({"unit_id": fetch_id, "status": "skipped_root_url", "url": url})
            print(f"SKIP root {fetch_id}")
            continue

        allowed, robots_note = robots_ok(url)
        if not allowed:
            results.append(
                {"unit_id": fetch_id, "status": "excluded_robots", "url": url,
                 "note": robots_note}
            )
            print(f"ROBOTS {fetch_id}")
            time.sleep(DELAY_S)
            continue

        time.sleep(DELAY_S)
        try:
            status, ct, body = fetch(url)
        except urllib.error.HTTPError as e:
            results.append(
                {"unit_id": fetch_id, "status": f"http_{e.code}", "url": url,
                 "note": robots_note}
            )
            print(f"HTTP {e.code} {fetch_id}")
            continue
        except Exception as e:
            results.append(
                {"unit_id": fetch_id, "status": "fetch_error", "url": url,
                 "note": f"{e}; {robots_note}"}
            )
            print(f"ERR  {fetch_id}: {e}")
            continue

        snap = RAW / f"{fetch_id}.html"
        snap.write_bytes(body)
        if "html" not in ct.lower():
            text = body.decode("utf-8", errors="replace")[:200_000]
        else:
            text = html_to_text(body.decode("utf-8", errors="replace"))
        (RAW / f"{fetch_id}.txt").write_text(text, encoding="utf-8", errors="replace")
        lic = extract_license_signals(text)
        years = extract_year_candidates(text)
        lic_status = classify_license(text, lic)
        results.append(
            {
                "unit_id": fetch_id,
                "status": "fetched",
                "http_status": status,
                "content_type": ct,
                "url": url,
                "robots_note": robots_note,
                "license_status": lic_status,
                "license_signals": lic,
                "year_candidates": years,
                "snapshot_html": str(snap.relative_to(ROOT)),
                "fetched_utc": datetime.now(timezone.utc).isoformat(),
                "text_chars": len(text),
            }
        )
        n_ok += 1
        print(f"OK   {fetch_id} lic={lic_status} years={years['years'][:8]} chars={len(text)}")

    with EVIDENCE.open("a", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"fetched_ok={n_ok} evidence_rows={len(results)} -> {EVIDENCE}")


if __name__ == "__main__":
    main()
