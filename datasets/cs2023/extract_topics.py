"""Extract Knowledge-Area topic terms from the CS2023 Body of Knowledge PDF text.

Input:  CS2023_BoK.txt (produced by `pdftotext -layout CS2023_BoK.pdf CS2023_BoK.txt`)
Output: cs2023_topics.csv  (ka_code, ka_name, ku_code, ku_name, topic)

The CSV is the CURR01 anchor list embedded into the Kaggle experiment script.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEXT = HERE / "CS2023_BoK.txt"
OUT = HERE / "cs2023_topics.csv"

KA_NAMES = {
    "AI": "Artificial Intelligence",
    "AL": "Algorithmic Foundations",
    "AR": "Architecture and Organization",
    "DM": "Data Management",
    "FPL": "Foundations of Programming Languages",
    "GIT": "Graphics and Interactive Techniques",
    "HCI": "Human-Computer Interaction",
    "MSF": "Mathematical and Statistical Foundations",
    "NC": "Networking and Communication",
    "OS": "Operating Systems",
    "PDC": "Parallel and Distributed Computing",
    "SDF": "Software Development Fundamentals",
    "SE": "Software Engineering",
    "SEC": "Security",
    "SEP": "Society, Ethics, and the Profession",
    "SF": "Systems Fundamentals",
    "SPD": "Specialized Platform Development",
}

KU_RE = re.compile(r"^\s*([A-Z]{2,4})-([A-Za-z][A-Za-z\-]*):\s*(\S.*)$")
TOPIC_RE = re.compile(r"^\s{0,4}(\d{1,2})\.\s+(\S.*)$")
SKIP_CORE = re.compile(r"^\s*(CS Core|KA Core|Tier 1|Tier 2)\s*:", re.I)
PAGE_NUM = re.compile(r"^\s*\d{1,3}\s*$")


LEAD_VERBS = re.compile(
    r"^\s*(?:Select|Implement|Design|Evaluate|Describe|Differentiate|Apply|Analyze|"
    r"Construct|Explain|Demonstrate|Justify|Compare|Develop|Identify|Summarize|Discuss|"
    r"List|Define|Trace|Classify|Recognize|Determine|Compute|Create|Use|Perform|Model|"
    r"Specify|Measure|Predict|Translate|Write|Read|Build|Select and implement)\s+",
    re.I,
)


def clean_topic(text: str) -> str:
    # drop "(See also: ...)" (possibly unbalanced at line end) then other parentheticals
    text = re.sub(r"\s*\(See also:.*$", "", text, flags=re.I)
    text = re.sub(r"\s*\([^)]*\)", "", text)
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = LEAD_VERBS.sub("", text)
    text = re.sub(r"\s+", " ", text).strip(" .,-")
    text = text.encode("ascii", "ignore").decode("ascii")
    return text


def main() -> None:
    text = TEXT.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    rows: list[tuple[str, str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    cur_ka = cur_ku_code = cur_ku_name = ""

    for line in lines:
        m_ku = KU_RE.match(line)
        if m_ku:
            ka, ku, name = m_ku.groups()
            if ka in KA_NAMES and len(name) > 3:
                cur_ka, cur_ku_code, cur_ku_name = ka, ku, name.strip()
            continue
        if not cur_ka or SKIP_CORE.match(line) or PAGE_NUM.match(line):
            continue
        m_t = TOPIC_RE.match(line)
        if m_t:
            topic = clean_topic(m_t.group(2))
            if (
                len(topic) < 3
                or len(topic) > 90
                or topic.isdigit()
                or topic.startswith(("Tier", "CS Core", "KA Core"))
            ):
                continue
            key = (cur_ka, cur_ku_code, topic.lower())
            if key in seen:
                continue
            seen.add(key)
            rows.append((cur_ka, KA_NAMES[cur_ka], cur_ku_code, cur_ku_name, topic))

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ka_code", "ka_name", "ku_code", "ku_name", "topic"])
        w.writerows(rows)

    per_ka: dict[str, int] = {}
    for r in rows:
        per_ka[r[0]] = per_ka.get(r[0], 0) + 1
    print(f"topics: {len(rows)} across {len(per_ka)} KAs")
    for ka in sorted(per_ka):
        print(f"  {ka}: {per_ka[ka]}")


if __name__ == "__main__":
    main()
