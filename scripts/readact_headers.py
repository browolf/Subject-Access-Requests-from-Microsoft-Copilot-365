"""
redact_headers.py — Email header and address redaction

Purpose
- Redacts identifying header information and email addresses from text
  extracted from Microsoft Purview SAR exports.
- Intended to reduce disclosure of third-party personal data before review.

Where it fits in the workflow
1) Export ZIPs from Purview
2) Extract PST using pffexport
3) Run filterv3.py
4) Run this script (redact_headers.py)
5) Run redact_words.py

What this script does
- Processes all .txt files under:
    output.export/
- Detects and redacts header lines including:

    sender name:
    sender email address:
    sent representing name:
    sent representing email address:
    from:
    to:
    cc:
    return-path:

- Handles multiline (folded) headers:
  Continuation lines beginning with whitespace are also redacted.

- Redacts ANY remaining email addresses found elsewhere in the text.

Redaction format
- Replaces values with:

    <redacted>

- Preserves indentation and line endings.

Inputs / Assumptions
- Text files generated from PST extraction + filterv3 stage
- Working directory:
    output.export/
- Files encoded as UTF-8 (errors ignored safely)

Outputs
- Files modified in place
- Uses temporary file replacement to reduce corruption risk

Dependencies
- Python 3.x
- Standard library only (re, pathlib)

Usage
Run from directory containing output.export:

    python redact_headers.py

Operational Notes
- Script is safe to rerun:
  - Already redacted content will not be altered further
- Designed to run after HTML→text conversion
- Does NOT redact names or other identifiers — that occurs in redact_words.py
- Operates on copies of exports, not originals

Repository Context
- See /docs/purview-export.md for export setup
- See filterv3.py for preprocessing stage
- See redact_words.py for content-level redaction
"""

import re
from pathlib import Path

RE_WHITESPACE = re.compile(r"\s+")
RE_EOL = re.compile(r"(\r?\n)$")
RE_INDENT = re.compile(r"^(\s*)")

# Strong email regex
RE_EMAIL = re.compile(
    r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+"
)

HEADER_FIELDS = [
    "sender name:",
    "sender email address:",
    "sent representing name:",
    "sent representing email address:",
    "from:",
    "to:",
    "cc:",
    "return-path:",
]

HEADER_PREFIXES = tuple(h.lower() for h in HEADER_FIELDS)

def get_eol(line: str):
    m = RE_EOL.search(line)
    return m.group(1) if m else ""

def is_header_field(line: str) -> bool:
    if ":" not in line:
        return False
    collapsed = RE_WHITESPACE.sub(" ", line.lower())
    return any(collapsed.startswith(prefix) for prefix in HEADER_PREFIXES)

def redact_header(line: str) -> str:
    eol = get_eol(line)
    base = line[:-len(eol)] if eol else line
    prefix, after = base.split(":", 1)
    ws = RE_INDENT.match(after).group(1)
    return f"{prefix}:{ws}<redacted>{eol}"

def redact_continuation(line: str) -> str:
    eol = get_eol(line)
    ws = RE_INDENT.match(line).group(1)
    return f"{ws}<redacted>{eol}"

def redact_emails(line: str) -> str:
    return RE_EMAIL.sub("<redacted>", line)

def process_txt(path: Path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    new_lines = []
    in_continuation = False
    changed = False

    for line in lines:

            if in_continuation:
                if line.startswith((" ", "\t")):
                    nl = redact_continuation(line)
                    nl = redact_emails(nl)
                    new_lines.append(nl)
                    changed = True
                    continue
                in_continuation = False

            if is_header_field(line):
                nl = redact_header(line)
                nl = redact_emails(nl)
                new_lines.append(nl)
                changed = True
                in_continuation = True
                continue

            # Apply email redaction to ALL other lines
            nl = redact_emails(line)
            if nl != line:
                changed = True
            new_lines.append(nl)

    if changed:
        print(f"[Headers redacted] {path}")
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8", errors="ignore") as f:
            f.writelines(new_lines)
        tmp.replace(path)

def main():
    root = Path("output.export")
    for p in root.rglob("*.txt"):
        process_txt(p)

if __name__ == "__main__":
    main()
