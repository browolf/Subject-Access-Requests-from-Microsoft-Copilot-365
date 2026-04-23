"""
================================================================================
redact_metadatav2.py
================================================================================

Metadata & Email Redaction Tool

This script post-processes merged PST export files and redacts sensitive
metadata and email addresses to support GDPR, SAR, and eDiscovery workflows.

It is designed to run AFTER filtering/merging (e.g. filterv5.py).

-------------------------------------------------------------------------------
What it does
-------------------------------------------------------------------------------
- Redacts common email header fields such as:
    • From:
    • To:
    • Cc:
    • Sender Name / Email
    • Return-Path
    • Sent Representing

- Handles multi-line (folded) headers correctly:
    → Continuation lines (indented lines) are also fully redacted

- Redacts ALL email addresses found anywhere in the content

- Preserves:
    • File structure
    • Line formatting and indentation
    • Original line endings (CRLF / LF)

- Outputs changes in-place (safe write via temporary file)

-------------------------------------------------------------------------------
Target Files
-------------------------------------------------------------------------------
By default processes:
    output.export/combined_messages.txt
    output.export/combined_appointments.txt
    output.export/combined_meetings.txt

-------------------------------------------------------------------------------
Key Features
-------------------------------------------------------------------------------
- Strong regex-based email detection
- Header-aware redaction (not just blind search/replace)
- Continuation-aware parsing (handles Outlook-style headers)
- Detailed console logging:
    [HEAD] Header redactions
    [CONT] Continuation redactions
    [EML ] Inline email redactions
- Safe file replacement (writes to .tmp before overwrite)

-------------------------------------------------------------------------------
Configuration
-------------------------------------------------------------------------------
REPLACEMENT = "<redacted>"
    → Change if required (e.g. HTML-safe "&lt;redacted&gt;")

TARGET_FILES
    → Modify paths if your output structure differs

-------------------------------------------------------------------------------
Typical Use Case
-------------------------------------------------------------------------------
- Subject Access Requests (SAR)
- GDPR compliance / data minimisation
- Preparing datasets for external sharing
- Internal investigations where identities must be masked

-------------------------------------------------------------------------------
Requirements
-------------------------------------------------------------------------------
- Python 3.x

(No external dependencies required)

-------------------------------------------------------------------------------
Usage
-------------------------------------------------------------------------------
    python redact_metadatav2.py

-------------------------------------------------------------------------------
Notes
-------------------------------------------------------------------------------
- Only modifies files if changes are detected
- Missing files are skipped with warnings
- Designed to be deterministic and repeatable

================================================================================
"""

import re
from pathlib import Path

# ---------- Configuration ----------
TARGET_FILES = [
    Path("output.export/combined_messages.txt"),
    Path("output.export/combined_appointments.txt"),
    Path("output.export/combined_meetings.txt"),
]
REPLACEMENT = "<redacted>"  # Change to "&lt;redacted&gt;" if you need HTML-escaped output

# ---------- Regexes ----------
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

# ---------- Helpers ----------
def get_eol(line: str) -> str:
    """Return the original EOL sequence, if any."""
    m = RE_EOL.search(line)
    return m.group(1) if m else ""

def is_header_field(line: str) -> bool:
    """Heuristically detect if the line begins with one of the header fields (case-insensitive, whitespace-tolerant)."""
    if ":" not in line:
        return False
    collapsed = RE_WHITESPACE.sub(" ", line.lower())
    return any(collapsed.startswith(prefix) for prefix in HEADER_PREFIXES)

def redact_header(line: str) -> str:
    """Replace the value part of a header line with <redacted>, preserving indentation and EOL."""
    eol = get_eol(line)
    base = line[:-len(eol)] if eol else line
    prefix, after = base.split(":", 1)
    ws = RE_INDENT.match(after).group(1)
    return f"{prefix}:{ws}{REPLACEMENT}{eol}"

def redact_continuation(line: str) -> str:
    """Redact a header continuation line (one that starts with space or tab), preserving indentation and EOL."""
    eol = get_eol(line)
    ws = RE_INDENT.match(line).group(1)
    return f"{ws}{REPLACEMENT}{eol}"

def redact_emails(line: str) -> str:
    """Redact email addresses anywhere in a line."""
    return RE_EMAIL.sub(REPLACEMENT, line)

# ---------- Core processing ----------
def process_file(path: Path) -> None:
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return
    if not path.is_file():
        print(f"[ERROR] Not a file: {path}")
        return

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    new_lines = []
    in_continuation = False
    changed = False

    print(f"[INFO] Redacting: {path}")
    for idx, line in enumerate(lines, start=1):
        original_line = line

        # Continuation block handling
        if in_continuation:
            if line.startswith((" ", "\t")):
                nl = redact_continuation(line)
                nl = redact_emails(nl)
                if nl != original_line:
                    changed = True
                    print(f"[CONT] L{idx}: {original_line.rstrip()} -> {nl.rstrip()}")
                new_lines.append(nl)
                continue
            # Next line is not indented => end of continuation block
            in_continuation = False

        # Header line handling
        if is_header_field(line):
            nl = redact_header(line)
            nl = redact_emails(nl)
            if nl != original_line:
                changed = True
                print(f"[HEAD] L{idx}: {original_line.rstrip()} -> {nl.rstrip()}")
            new_lines.append(nl)
            in_continuation = True
            continue

        # Non-header lines: redact any emails
        nl = redact_emails(line)
        if nl != original_line:
            changed = True
            print(f"[EML ] L{idx}: {original_line.rstrip()} -> {nl.rstrip()}")
        new_lines.append(nl)

    if changed:
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8", errors="ignore") as f:
            f.writelines(new_lines)
        tmp.replace(path)
        print(f"[DONE] Changes written to {path}")
    else:
        print("[DONE] No changes needed.")

def main():
    for p in TARGET_FILES:
        process_file(p)

if __name__ == "__main__":
    main()
