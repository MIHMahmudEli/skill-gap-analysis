"""Probe candidate curriculum URLs before committing them to MANIFEST.csv.

This is a *read-only* reconnaissance tool. It never writes to the manifest and
never extracts skills -- it only reports, per candidate URL, whether the page
exists and (optionally) the signals you need to fill the manifest by hand:
material year, license, and character count.

It consolidates the three ad-hoc probes that were used during Phase 1
(`_probe_urls.py`, `_probe_more.py`, `_probe_more2.py`) into one documented
entry point with named candidate sets.

Two modes
---------
exist   (default)  HTTP status only. Fast; use to prune dead URLs.
meta               Also strips boilerplate and extracts publication year,
                   "As Taught In" term, course-code|term pairs, and whether a
                   Creative Commons signal is present. Use to fill
                   material_year / vintage_group / license columns by hand.

Usage
-----
    python datasets/curriculum/probe_urls.py                     # all sets, exist
    python datasets/curriculum/probe_urls.py --mode meta         # all sets, metadata
    python datasets/curriculum/probe_urls.py --sets mit6009 harv
    python datasets/curriculum/probe_urls.py --urls https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/

Notes
-----
* Candidates below are historical probes. Several were superseded once the
  syllabus sub-page (`.../pages/syllabus`) was found to carry richer content
  than the course landing page; the ones actually adopted live in MANIFEST.csv.
* Network access required. Polite 1s delay between requests, academic UA.
* Nothing here is analysis-driven; it only reads public pages.
"""
from __future__ import annotations

import argparse
import re
import ssl
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser

try:
    import certifi

    _CA = certifi.where()
except Exception:  # pragma: no cover - certifi always present in verified env
    _CA = None

CTX = ssl.create_default_context(cafile=_CA) if _CA else ssl.create_default_context()
UA = "skill-gap-curriculum-research/1.0 (academic; polite; contact: repo owner via GitHub)"
DELAY_S = 1.0

# --- candidate sets -------------------------------------------------------
# Keys are stable set names; values map a working label -> URL. Labels are
# probe-local and do NOT have to match MANIFEST unit_id (a probe may try
# several term-variants of one course under suffixed labels).
CANDIDATES: dict[str, dict[str, str]] = {
    "urls": {  # original existence sweep (dead-vs-alive pruning)
        "MIT-6009-f16": "https://ocw.mit.edu/courses/6-009-fundamentals-of-programming-fall-2016/",
        "MIT-6009-f11": "https://ocw.mit.edu/courses/6-009-fundamentals-of-programming-fall-2011/",
        "MIT-6009-f12": "https://ocw.mit.edu/courses/6-009-fundamentals-of-programming-fall-2012/",
        "MIT-6031-s16": "https://ocw.mit.edu/courses/6-031-software-construction-spring-2016/",
        "MIT-6031-s13": "https://ocw.mit.edu/courses/6-031-software-construction-spring-2013/",
        "MIT-6031-s11": "https://ocw.mit.edu/courses/6-031-software-construction-spring-2011/",
        "MIT-6034-f10": "https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010",
        "MIT-6034-f10-syll": "https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/pages/syllabus",
        "MIT-6036-f20": "https://ocw.mit.edu/courses/6-036-introduction-to-machine-learning-fall-2020",
        "MIT-6036-f16": "https://ocw.mit.edu/courses/6-036-introduction-to-machine-learning-fall-2016/",
        "MIT-6041-s14": "https://ocw.mit.edu/courses/6-041-science-of-probability-spring-2014",
        "MIT-6041-s13": "https://ocw.mit.edu/courses/6-041-science-of-probability-spring-2013/",
        "MIT-6041-f11": "https://ocw.mit.edu/courses/6-041-science-of-probability-fall-2011/",
        "MIT-6824-f20": "https://ocw.mit.edu/courses/6-824-distributed-systems-spring-2020/",
        "MIT-6824-s06": "https://ocw.mit.edu/courses/6-824-distributed-computer-systems-engineering-spring-2006/",
        "MIT-6100L-f22": "https://ocw.mit.edu/courses/6-100l-introduction-to-cs-and-programming-using-python-fall-2022/",
        "MIT-6033-s18": "https://ocw.mit.edu/courses/6-033-computer-system-engineering-spring-2018/",
        "HARV-AI-lic": "https://cs50.harvard.edu/ai/license/",
        "HARV-AI-2024": "https://cs50.harvard.edu/ai/2024/x/",
        "HARV-AI-2025": "https://cs50.harvard.edu/ai/2025/x/",
        "HARV-PY-syll-2022": "https://cs50.harvard.edu/python/2022/x/syllabus/",
        "HARV-PY-syll": "https://cs50.harvard.edu/python/syllabus/",
        "HARV-PY": "https://cs50.harvard.edu/python/",
        "HARV-X-syll-2026": "https://cs50.harvard.edu/x/2026/syllabus/",
        "CMU-OLI-interpreting-data": "https://oli.cmu.edu/courses/interpreting-data/",
        "CMU-OLI-python": "https://oli.cmu.edu/courses/programming-in-python/",
        "CMU-OLI-how-to-code": "https://oli.cmu.edu/courses/how-to-code-fundamentals/",
        "OU-intro-computing": "https://www.open.edu/openlearn/computing-and-it/introduction-computing-and-it",
        "OU-education-studies": "https://www.open.edu/openlearn/education-development/introduction-to-education-studies",
        "OU-intro-algebra": "https://www.open.edu/openlearn/science-maths-technology/introduction-algebra",
        "SEE-lic": "https://see.stanford.edu/UsingSEE",
        "SEE-CS107": "https://see.stanford.edu/Course/CS107",
    },
    "more": {  # broader subject sweep (fill strata gaps)
        "TUD-AIPP": "https://ocw.tudelft.nl/courses/ai-in-practice-preparing-for-ai/",
        "TUD-OOP": "https://ocw.tudelft.nl/courses/object-oriented-programming/",
        "TUD-DATASCI": "https://ocw.tudelft.nl/courses/introduction-to-data-science/",
        "TUD-NET": "https://ocw.tudelft.nl/courses/computer-networks/",
        "TUD-ARCH": "https://ocw.tudelft.nl/courses/computer-architecture/",
        "TUD-DB": "https://ocw.tudelft.nl/courses/databases/",
        "TUD-SE": "https://ocw.tudelft.nl/courses/software-engineering/",
        "MIT-6172-f18": "https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/",
        "MIT-6035-f18": "https://ocw.mit.edu/courses/6-035-computer-language-engineering-fall-2018/",
        "MIT-6046-s12": "https://ocw.mit.edu/courses/6-046j-design-and-analysis-of-algorithms-spring-2012/",
        "MIT-6042-f15": "https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-fall-2015/",
        "MIT-6004-s17": "https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/",
        "MIT-6047-f15": "https://ocw.mit.edu/courses/6-047-computational-biology-fall-2015/",
        "MIT-6049-f15": "https://ocw.mit.edu/courses/6-049-interactive-robotics-fall-2015/",
        "MIT-6005-f12": "https://ocw.mit.edu/courses/6-005-elements-of-software-construction-fall-2012/",
        "MIT-6037-s12": "https://ocw.mit.edu/courses/6-037-artificial-intelligence-spring-2012/",
        "MIT-6854-f08": "https://ocw.mit.edu/courses/6-854j-advanced-algorithms-fall-2008/",
    },
    "more2": {  # syllabus-subpage sweep (richer content than landing pages)
        "TUD-DABIZ": "https://ocw.tudelft.nl/courses/data-analysis-building-your-own-business-dashboard/",
        "TUD-DAMAX": "https://ocw.tudelft.nl/courses/data-analysis-take-it-to-the-max/",
        "TUD-DAVIZ": "https://ocw.tudelft.nl/courses/data-analysis-visualization-and-dashboard-design/",
        "TUD-QB1": "https://ocw.tudelft.nl/courses/the-building-blocks-of-a-quantum-computer-part-1/",
        "TUD-QB2": "https://ocw.tudelft.nl/courses/the-building-blocks-of-a-quantum-computer-part-2/",
        "TUD-SCRATCHT": "https://ocw.tudelft.nl/courses/scratch-programming-for-teachers/",
        "TUD-SCRATCHK": "https://ocw.tudelft.nl/courses/scratch-programming-for-kids-8/",
        "MIT-6100B-f22": "https://ocw.mit.edu/courses/6-100b-introduction-to-computational-thinking-using-python-fall-2022/",
        "MIT-6034-f10-syll": "https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/pages/syllabus",
        "MIT-1806-s10-syll": "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/pages/syllabus",
        "MIT-6046-s15-syll": "https://ocw.mit.edu/courses/6-046j-design-and-analysis-of-algorithms-spring-2015/pages/syllabus",
        "MIT-6001-s05": "https://ocw.mit.edu/courses/6-001-structure-and-interpretation-of-computer-programs-spring-2005/",
        "MIT-6092-j-f06": "https://ocw.mit.edu/courses/6-092-j-introduction-to-biological-engineering-fall-2006/",
        "MIT-6170-s13": "https://ocw.mit.edu/courses/6-170-software-studio-spring-2013/",
        "MIT-6046-s12-syll": "https://ocw.mit.edu/courses/6-046j-design-and-analysis-of-algorithms-spring-2012/pages/syllabus",
        "MIT-6047-f15-syll": "https://ocw.mit.edu/courses/6-047-computational-biology-fall-2015/pages/syllabus",
        "MIT-6172-f18-syll": "https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/pages/syllabus",
        "MIT-6004-s17-syll": "https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/pages/syllabus",
        "MIT-6003-f11": "https://ocw.mit.edu/courses/6-003-signals-and-systems-fall-2011/",
        "MIT-6824-s06-syll": "https://ocw.mit.edu/courses/6-824-distributed-computer-systems-engineering-spring-2006/pages/syllabus",
        "MIT-6837-f12": "https://ocw.mit.edu/courses/6-837-computer-graphics-fall-2012/",
        "MIT-6828-f12-syll": "https://ocw.mit.edu/courses/6-828-operating-system-engineering-fall-2012/pages/syllabus",
        "MIT-6033-s18-syll": "https://ocw.mit.edu/courses/6-033-computer-system-engineering-spring-2018/pages/syllabus",
        "MIT-6046-s08-syll": "https://ocw.mit.edu/courses/6-046j-design-and-analysis-of-algorithms-spring-2008/pages/syllabus",
        "MIT-6046-s15": "https://ocw.mit.edu/courses/6-046j-design-and-analysis-of-algorithms-spring-2015/",
        "MIT-6042-f10-syll": "https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-fall-2010/pages/syllabus",
        "MIT-6042-s15": "https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-spring-2015/",
        "MIT-6006-s20": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/",
        "MIT-6006-s08": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-08/",
        "MIT-6005-f11": "https://ocw.mit.edu/courses/6-005-elements-of-software-construction-fall-2011/",
        "MIT-6005-f08": "https://ocw.mit.edu/courses/6-005-elements-of-software-construction-fall-2008/",
        "MIT-6034-s05": "https://ocw.mit.edu/courses/6-034-artificial-intelligence-spring-2005/",
        "MIT-6036-f20-syll": "https://ocw.mit.edu/courses/6-036-introduction-to-machine-learning-fall-2020/pages/syllabus",
        "MIT-6100L-f22-syll": "https://ocw.mit.edu/courses/6-100l-introduction-to-cs-and-programming-using-python-fall-2022/pages/syllabus",
        "MIT-18S191-f22-syll": "https://ocw.mit.edu/courses/18-s191-introduction-to-computational-thinking-fall-2022/pages/syllabus",
        "MIT-1805-s22-syll": "https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/pages/syllabus",
        "MIT-18404J-f20-syll": "https://ocw.mit.edu/courses/18-404j-theory-of-computation-fall-2020/pages/syllabus",
    },
}


class _TextExtractor(HTMLParser):
    """Strip scripts/styles and collapse whitespace -> flat text."""

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


def to_text(html: str) -> str:
    p = _TextExtractor()
    try:
        p.feed(html)
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", " ".join(p.parts)).strip()


def probe_meta(text: str) -> str:
    pub = re.findall(r"Publication:\s*([0-9-]+)", text)
    taught = re.findall(r"As Taught In\s+([A-Za-z]+ 20[0-9]{2})", text)
    code_year = re.findall(r"([A-Z]{2,4}[- ]?\d+\w*)\s*\|\s*([A-Za-z]+ 20[0-9]{2})", text)
    pipe = re.findall(r"\|\s*([A-Za-z]+ 20[0-9]{2})", text)
    cc = any(
        k in text.lower()
        for k in ("cc by", "creative commons", "attribution-noncommercial")
    )
    return (
        f"pub={pub[:2]} taught={taught[:1]} code_year={code_year[:2]} "
        f"pipe={pipe[:3]} cc={cc} chars={len(text)}"
    )


def probe_one(label: str, url: str, mode: str) -> str:
    if not url.startswith("http"):
        return f"BAD  {label} {url!r} (not an http URL)"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en",
            },
        )
        with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
            if mode == "exist":
                return f"OK   {r.status} {label} {url}"
            body = r.read(500_000)
            text = to_text(body.decode("utf-8", errors="replace"))
            return f"OK   {r.status} {label} {probe_meta(text)}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code} {label} {url}"
    except Exception as e:
        return f"ERR  {label} {url} ({type(e).__name__}: {e})"


def iter_targets(sets: list[str], extra_urls: list[str]):
    if extra_urls:
        for i, u in enumerate(extra_urls, 1):
            yield f"arg{i}", u
        return
    for name in sets:
        for label, url in CANDIDATES[name].items():
            yield label, url


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Probe curriculum candidate URLs (read-only, never writes)."
    )
    ap.add_argument(
        "--sets", nargs="*", default=sorted(CANDIDATES),
        choices=sorted(CANDIDATES), help="candidate sets to probe",
    )
    ap.add_argument(
        "--urls", nargs="*", default=[],
        help="probe explicit URLs instead of the built-in sets",
    )
    ap.add_argument(
        "--mode", choices=["exist", "meta"], default="exist",
        help="exist = HTTP status only; meta = also extract year/license signals",
    )
    ap.add_argument("--delay", type=float, default=DELAY_S, help="seconds between requests")
    args = ap.parse_args()

    n_ok = n_bad = 0
    for label, url in iter_targets(args.sets, args.urls):
        line = probe_one(label, url, args.mode)
        print(line)
        if line.startswith("OK"):
            n_ok += 1
        else:
            n_bad += 1
        time.sleep(args.delay)
    print(f"\nok={n_ok} not_ok={n_bad} mode={args.mode}")


if __name__ == "__main__":
    main()
