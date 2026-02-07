"""
redact_words.py — Iterative keyword/phrase redaction from extracted SAR text

Purpose
- Redacts user-specified words and phrases from .txt files produced during
  SAR processing (after PST extraction and preprocessing).
- Supports iterative review: update redact_words.txt and rerun until satisfied.

Where it fits in the workflow
1) Export ZIPs from Purview
2) Extract PST using pffexport
3) Run filterv3.py
4) Run redact_headers.py
5) Run this script (redact_words.py)

What this script does
- Loads a redaction list from:
    redact_words.txt
  (one word/phrase per line; blank lines ignored)
- Processes all .txt files under:
    output.export/
- Replaces matches with:
    <redacted>
- Prints per-file reporting showing which terms were redacted.

Matching behaviour
- Case-insensitive matching.
- Uses a whole-word boundary pattern (\\b...\\b).
  This is ideal for single words.
  Note: for multi-word phrases, word-boundary behaviour still applies at the
  phrase edges, but may not match across punctuation/line breaks.

Inputs / Assumptions
- Working directory contains:
    output.export/
    redact_words.txt
- redact_words.txt is UTF-8 encoded.

Outputs
- Files modified in place under output.export/
- Uses temporary file replacement to reduce corruption risk
- Console output lists matched terms per file

Dependencies
- Python 3.x
- Standard library only (re, pathlib)

Usage
Run from the directory containing output.export and redact_words.txt:

    python redact_words.py

Operational Notes
- Designed to be rerun safely:
  - You can keep adding terms to redact_words.txt and rerun the script.
- This script does not attempt semantic redaction—only explicit terms in the list.
- For best results, run after redact_headers.py so addresses/headers are already removed.

Repository Context
- See /docs/purview-export.md for export setup
- See filterv3.py for preprocessing stage
- See redact_headers.py for header/email address redaction stage

"""

import re
from pathlib import Path

# Load list of words/phrases to redact (one per line)
def load_redaction_list(file_path: Path):
    if not file_path.exists():
        print(f"Redaction file not found: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


# Build whole-word case-insensitive regex
def build_word_regex(words):
    pattern = r"\b(" + "|".join(re.escape(w) for w in words) + r")\b"
    return re.compile(pattern, re.IGNORECASE)


# Redact words (output <redacted> in file)
# Collect original words for console reporting
def redact_words(line: str, re_words, hits: set) -> str:
    def replacer(match):
        hits.add(match.group(0))    # collect actual matched word
        return "<redacted>"

    return re_words.sub(replacer, line)


def process_txt(path: Path, re_words):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    new_lines = []
    changed = False
    hits = set()  # store words redacted in this file

    for line in lines:
        new_line = redact_words(line, re_words, hits)
        if new_line != line:
            changed = True
        new_lines.append(new_line)

    if changed:
        # Print which words were redacted
        hit_list = ", ".join(sorted(hits))
        print(f"[Words redacted] {path} → {hit_list}")

        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8", errors="ignore") as f:
            f.writelines(new_lines)
        tmp.replace(path)


def main():
    root = Path("output.export")
    redact_file = Path("redact_words.txt")

    words = load_redaction_list(redact_file)

    if not words:
        print("No words loaded — nothing to redact.")
        return

    re_words = build_word_regex(words)

    for p in root.rglob("*.txt"):
        process_txt(p, re_words)


if __name__ == "__main__":
    main()


