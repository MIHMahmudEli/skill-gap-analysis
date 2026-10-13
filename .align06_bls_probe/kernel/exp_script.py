"""ALIGN06 pre-download probe: is www.bls.gov reachable from a Kaggle kernel?

The author's host is IP-blocked by BLS (403 on every host/path/stack). A Kaggle
kernel has a different egress and already proved it can reach huggingface.co.
This probe only records reachability, status, size and SHA-256; it writes nothing
outside /kaggle/working and performs at most one full download.
"""
from __future__ import annotations

import hashlib
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

UA = ("skill-gap-analysis/1.0 (reproducibility audit; "
      "https://github.com/MIHMahmudEli/skill-gap-analysis; "
      "contact: mdmohsin11222@gmail.com)")

HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# (label, url, download?)  - download only for the single archive we actually need.
TARGETS = [
    ("oews_nat_archive", "https://www.bls.gov/oes/special-requests/oesm25nat.zip", True),
    ("bls_robots", "https://www.bls.gov/robots.txt", False),
    ("bls_copyright_page", "https://www.bls.gov/opub/copyright-information.htm", False),
    ("oe_ws_tables", "https://www.bls.gov/oes/tables.htm", False),
    ("onet_db_30_0_control", "https://www.onetcenter.org/dl_files/database/db_30_0_text.zip", False),
]

WORKDIR = "/kaggle/working"
OUT = os.path.join(WORKDIR, "probe.json")


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(label: str, url: str, download: bool) -> dict:
    rec = {"label": label, "url": url, "download": download, "ts": now()}
    req = urllib.request.Request(url, headers=HEADERS)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120, context=ssl.create_default_context()) as resp:
            rec["status"] = resp.status
            rec["server"] = resp.headers.get("Server")
            rec["content_type"] = resp.headers.get("Content-Type")
            rec["content_length"] = resp.headers.get("Content-Length")
            rec["last_modified"] = resp.headers.get("Last-Modified")
            if download:
                dest = os.path.join(WORKDIR, os.path.basename(url))
                total = 0
                h = hashlib.sha256()
                with open(dest, "wb") as fh:
                    while True:
                        chunk = resp.read(1 << 20)
                        if not chunk:
                            break
                        fh.write(chunk)
                        h.update(chunk)
                        total += len(chunk)
                rec["bytes"] = total
                rec["sha256"] = h.hexdigest()
                rec["saved_to"] = dest
            else:
                body = resp.read(4096)
                rec["head_bytes"] = len(body)
                rec["head_preview"] = body[:200].decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        rec["status"] = e.code
        rec["http_error"] = str(e.reason)
        try:
            rec["body_preview"] = e.read()[:400].decode("utf-8", "replace")
        except Exception:
            pass
    except Exception as e:
        rec["error"] = "%s: %s" % (type(e).__name__, e)
    rec["elapsed_sec"] = round(time.time() - t0, 3)
    return rec


def main() -> int:
    results = []
    for label, url, download in TARGETS:
        print("== %s -> %s" % (label, url), flush=True)
        r = probe(label, url, download)
        print("   %s" % json.dumps({k: v for k, v in r.items()
                                    if k not in ("head_preview", "body_preview")}),
              flush=True)
        results.append(r)
        # one polite pause between requests
        time.sleep(2)

    summary = {
        "probe": "ALIGN06 BLS reachability from a Kaggle CPU kernel",
        "ts": now(),
        "kernel_env": {
            "python": sys.version.split()[0],
            "cwd": os.getcwd(),
        },
        "results": results,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    print("wrote %s" % OUT, flush=True)

    ok = [r for r in results if r.get("status") == 200]
    print("reachable: %d/%d" % (len(ok), len(results)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
