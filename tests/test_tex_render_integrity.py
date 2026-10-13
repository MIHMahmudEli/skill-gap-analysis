"""LaTeX render integrity: the source must actually reach the PDF.

Two defects were shipped in the abstract rewrite (commit ``e6bcf48``) and
survived every gate, because every gate reads the ``.tex`` **source** and none
of them reads the rendered PDF:

1. ``%`` unescaped in ``52.0%``. In LaTeX ``%`` starts a comment, so the first
   one commented out the remaining 909 characters of the abstract -- 142 words.
   The headline result, the SENS01 ranges, the CS2023 anchor and the ESCO
   validation never appeared in ``main.pdf``; pdftotext stopped at
   ``SGI) of 52.0`` and the next words in the document were ``Index Terms``.
2. ``&`` unescaped in ``Programming & Development``. LaTeX raised
   ``! Misplaced alignment tab character &.`` and dropped the ampersand, so the
   PDF read ``Programming Development`` -- while ``verify_claims`` kept passing,
   because it pins the literal against the source.

A third, related defect: ``tau``/``kappa``/``in``/``geq`` have no glyph in the
T1 text font. Left undeclared, pdflatex raised ``LaTeX Error: Unicode
character`` and silently dropped them; they are now declared in the preamble.

The baseline abstracts (``9ca13e2``, ``0aa1ac2``) had zero unescaped ``%`` and
their ``&`` escaped, so this is a regression these tests pin.

No network, no PDF toolchain required -- these are source-level invariants.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MAIN = ROOT / "paper" / "main.tex"
PLACEMENT = ROOT / "paper_placement" / "main.tex"

# Environments in which a raw '&' is a legitimate column separator.
ALIGN_ENVS = frozenset({
    "tabular", "tabularx", "array", "IEEEeqnarray",
    "align", "aligned", "eqnarray", "cases", "split", "matrix", "pmatrix",
})

# Characters inputenc/utf8 already maps without help (kept as prose).
INPUTENC_NATIVE = frozenset({"\u2014", "\u2013", "\u2018", "\u2019",
                             "\u201c", "\u201d", "\u00a0"})


def _abstract_span(text: str) -> tuple[int, int]:
    """Return (start_line, end_line) indices of the abstract body, inclusive."""
    lines = text.split("\n")
    start = next(i for i, ln in enumerate(lines) if "\\begin{abstract}" in ln)
    end = next(i for i, ln in enumerate(lines) if "\\end{abstract}" in ln)
    return start + 1, end - 1


def _unescaped(line: str, char: str) -> list[int]:
    """Column offsets of `char` on `line` that are not preceded by a backslash."""
    if line.lstrip().startswith("%"):
        return []          # whole-line comment
    hits = []
    for i, c in enumerate(line):
        if c == char and (i == 0 or line[i - 1] != "\\"):
            hits.append(i)
    return hits


def _skip_continuation(line: str, col: int) -> bool:
    r"""True for the idiomatic `...{%` / `\end{tabular}%` line join.

    Those '%' deliberately comment out the newline so the next line is joined
    without a spurious space; they are intentional and must not be reported.
    """
    return line[col + 1:].strip() == "" and line[:col].endswith(("{", "}"))


def test_abstract_percent_signs_are_escaped():
    """An unescaped '%' silently truncates the abstract from that point on.

    This is the defect that removed 142 words from the rendered PDF while
    ``verify_claims`` continued to report 103/103.
    """
    for path in (MAIN, PLACEMENT):
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").split("\n")
        start, end = _abstract_span(path.read_text(encoding="utf-8"))
        for i in range(start, end + 1):
            bad = [c for c in _unescaped(lines[i], "%")]
            assert not bad, (
                f"{path.name} L{i + 1}: {len(bad)} unescaped '%'. In LaTeX this "
                f"comments out the rest of the line, so the abstract would be "
                f"truncated in the rendered PDF. Escape it as '\\%'."
            )


def test_abstract_ampersands_are_escaped():
    """An unescaped '&' is a misplaced alignment tab; LaTeX drops it.

    The defect rendered ``Programming  Development`` instead of
    ``Programming & Development`` while the source check still passed.
    """
    text = MAIN.read_text(encoding="utf-8")
    lines = text.split("\n")
    start, end = _abstract_span(text)
    for i in range(start, end + 1):
        bad = _unescaped(lines[i], "&")
        assert not bad, (
            f"paper/main.tex L{i + 1}: unescaped '&' in the abstract at column(s) "
            f"{bad}. LaTeX raises 'Misplaced alignment tab character' and drops "
            f"the ampersand from the PDF. Escape it as '\\&'."
        )


def test_no_unescaped_ampersand_in_running_prose():
    """Scan both manuscripts for stray '&' outside any alignment environment.

    Inside ``tabular`` a raw '&' is correct; in prose it must be '\\&'.
    """
    for path in (MAIN, PLACEMENT):
        if not path.exists():
            continue
        depth = 0
        for i, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            for m in re.finditer(r"\\(begin|end)\{(\w+\*?)\}", line):
                kind, name = m.group(1), m.group(2)
                if name in ALIGN_ENVS:
                    depth = depth + 1 if kind == "begin" else max(0, depth - 1)
            if depth:
                continue
            for col in _unescaped(line, "&"):
                if _skip_continuation(line, col):
                    continue
                assert False, (
                    f"{path.relative_to(ROOT)} L{i}: unescaped '&' in running "
                    f"prose (outside any tabular/align environment). It must be "
                    f"'\\&' or the PDF will drop it."
                )


def test_non_ascii_characters_are_declared_or_native():
    """Every non-ASCII character must be declared, or pdflatex drops it.

    ``tau``/``kappa``/``in``/``geq`` have no T1 glyph. Undeclared they raise
    ``LaTeX Error: Unicode character`` and vanish from the PDF -- which is what
    happened to ``tau`` and ``in`` for a full batch.
    """
    text = MAIN.read_text(encoding="utf-8")
    declared = {m.group(1).upper() for m in
                re.finditer(r"\\DeclareUnicodeCharacter\{([0-9A-Fa-f]{4})\}", text)}
    stray = set()
    for ch in text:
        cp = ord(ch)
        if cp < 128 or ch in INPUTENC_NATIVE:
            continue
        if f"{cp:04X}" in declared:
            continue
        stray.add(ch)
    assert not stray, (
        "paper/main.tex uses non-ASCII characters that are neither declared via "
        "\\DeclareUnicodeCharacter nor native to inputenc/utf8; pdflatex will "
        f"raise 'LaTeX Error: Unicode character' and drop them: "
        f"{sorted(f'U+{ord(c):04X}' for c in stray)}"
    )

    # Note: a companion check asserting every declaration is *used* was
    # deliberately omitted. The '2265' (>=) declaration lands in the commit
    # that introduces the symbol in the abstract, so "declared but unused" is
    # a legitimate transient state across two consecutive commits, and
    # asserting against it would make the suite order-dependent. An unused
    # declaration is harmless dead config; an *undeclared* character above
    # silently vanishes from the PDF, which is what the assertion above
    # actually protects.
