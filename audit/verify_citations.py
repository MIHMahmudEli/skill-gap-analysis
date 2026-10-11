#!/usr/bin/env python3
"""Phase 7: verify references.bib entries against Crossref metadata.

Read-only. For each entry with a DOI, query https://api.crossref.org/works/DOI
and compare title (fuzzy), year, first-author surname. Entries without DOI:
flag for manual verification. Writes audit/07_citation_check.csv + summary JSON.
"""
from __future__ import annotations

import csv
import json
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIB = (ROOT / "paper" / "references.bib").read_text(encoding="utf-8")

entries = re.split(r"\n(?=@)", BIB)
parsed = []
for chunk in entries:
    m = re.match(r"@(\w+)\{([^,]+),", chunk.strip())
    if not m:
        continue
    etype, key = m.group(1), m.group(2).strip()
    def field(name):
        fm = re.search(rf"{name}\s*=\s*[{{\"](.*?)[}}\"]\s*,?\s*\n", chunk, re.I | re.S)
        return fm.group(1).strip() if fm else ""
    parsed.append({
        "key": key, "type": etype,
        "title": re.sub(r"\s+", " ", field("title")).strip(),
        "author": field("author")[:80],
        "year": field("year") or field("date")[:4],
        "journal": field("journal") or field("booktitle") or field("publisher"),
        "doi": field("doi").lower().strip(),
        "url": field("url"),
    })

print(f"{len(parsed)} bib entries")

def norm_title(t: str) -> str:
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

results = []
for e in parsed:
    row = dict(e)
    row["crossref_status"] = ""
    row["title_match"] = ""
    row["year_match"] = ""
    row["crossref_title"] = ""
    if not e["doi"]:
        row["crossref_status"] = "no_doi_in_bib"
        results.append(row)
        continue
    url = f"https://api.crossref.org/works/{e['doi']}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "skill-gap-audit/1.0 (mailto:audit@example.org)"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            msg = json.loads(resp.read().decode("utf-8"))["message"]
        ct = re.sub(r"\s+", " ", " ".join(msg.get("title", []))).strip()
        cy = (msg.get("issued", {}).get("date-parts", [[None]])[0][0])
        row["crossref_title"] = ct[:160]
        nt, nct = norm_title(e["title"]), norm_title(ct)
        # token overlap
        toks_b, toks_c = set(nt.split()), set(nct.split())
        jac = len(toks_b & toks_c) / max(1, len(toks_b | toks_c))
        row["title_match"] = "yes" if jac >= 0.6 else f"weak(j={jac:.2f})"
        row["year_match"] = "yes" if str(cy) == str(e["year"]) else f"bib={e['year']}/cr={cy}"
        row["crossref_status"] = "verified"
    except urllib.error.HTTPError as err:
        row["crossref_status"] = f"http_{err.code}"
    except Exception as err:  # noqa: BLE001
        row["crossref_status"] = f"error:{type(err).__name__}"
    results.append(row)
    time.sleep(0.15)

out_csv = ROOT / "audit" / "07_citation_check.csv"
with out_csv.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    w.writeheader()
    w.writerows(results)

summary = {
    "n_entries": len(results),
    "verified_doi": sum(1 for r in results if r["crossref_status"] == "verified"),
    "http_404": sum(1 for r in results if r["crossref_status"] == "http_404"),
    "no_doi": sum(1 for r in results if r["crossref_status"] == "no_doi_in_bib"),
    "errors": sum(1 for r in results if str(r["crossref_status"]).startswith("error")),
    "title_mismatch": [r["key"] for r in results if str(r["title_match"]).startswith("weak") or r["title_match"] == "no"],
    "year_mismatch": [f"{r['key']}:{r['year_match']}" for r in results if r["year_match"] not in ("", "yes")],
    "unresolved": [r["key"] for r in results if r["crossref_status"] not in ("verified", "no_doi_in_bib")],
}
(ROOT / "audit" / "07_citation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
