"""
================================================================================
redact_wordsv3.py
================================================================================

Custom Word & Name Redaction Tool

This script performs targeted redaction of specific words and phrases across
processed PST export files. It is typically used AFTER metadata redaction
(e.g. redact_metadatav2.py) to remove identifiable names or sensitive terms.

-------------------------------------------------------------------------------
What it does
-------------------------------------------------------------------------------
- Redacts user-defined words and phrases (case-insensitive)
- Supports:
    • Single words (e.g. "John")
    • Multi-word phrases (e.g. "John Smith")
- Ensures whole-word matching (prevents partial replacements)
- Replaces matches with:
    → "<redacted>"

- Tracks and logs all matched terms per file

-------------------------------------------------------------------------------
Input Sources
-------------------------------------------------------------------------------
Words are loaded from:
    • redact_words.txt      → custom redaction list
    • school_staff.txt      → staff names list

(One entry per line)

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
- Case-insensitive matching with word boundaries
- Handles multi-word phrases safely
- Aggregates and logs all matched terms:
    [Words redacted] file → term1, term2, term3
- Safe file replacement using temporary file write
- Skips files that do not exist
- No external dependencies required

-------------------------------------------------------------------------------
Typical Use Case
-------------------------------------------------------------------------------
- Redacting staff/student names for GDPR compliance
- Removing sensitive keywords before data sharing
- Final sanitisation stage in SAR / eDiscovery workflows

-------------------------------------------------------------------------------
Requirements
-------------------------------------------------------------------------------
- Python 3.x

-------------------------------------------------------------------------------
Usage
-------------------------------------------------------------------------------
    python redact_wordsv3.py

-------------------------------------------------------------------------------
Notes
-------------------------------------------------------------------------------
- If no word lists are found or empty, script will exit safely
- Matching is strict (word boundaries used), so substrings are not redacted
- Can be extended to process all combined_*.txt files (see optional section)

================================================================================
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
# Supports multi-word entries (e.g., "John Smith")
def build_word_regex(words):
    # If nothing to build, return None for caller to handle
    if not words:
        return None
    # Escape + join each entry with alternation, wrap with word boundaries
    pattern = r"\b(" + "|".join(re.escape(w) for w in words) + r")\b"
    return re.compile(pattern, re.IGNORECASE)

# Redact words (output <redacted> in file)
# Collect original words for console reporting
def redact_words(line: str, re_words, hits: set) -> str:
    def replacer(match):
        hits.add(match.group(0))  # capture matched word (original case)
        return "<redacted>"
    return re_words.sub(replacer, line)

def process_txt(path: Path, re_words):
    if not path.exists():
        print(f"File not found: {path}")
        return

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    new_lines = []
    changed = False
    hits = set()

    for line in lines:
        new_line = redact_words(line, re_words, hits)
        if new_line != line:
            changed = True
        new_lines.append(new_line)

    if changed:
        hit_list = ", ".join(sorted(hits)) if hits else "(matched but could not list terms)"
        print(f"[Words redacted] {path} → {hit_list}")
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8", errors="ignore") as f:
            f.writelines(new_lines)
        tmp.replace(path)
    else:
        print(f"No redactions needed in: {path}")

def main():
    base = Path("output.export")
    targets = [
        base / "combined_messages.txt",
        base / "combined_appointments.txt",
        base / "combined_meetings.txt",
    ]

    redact_file = Path("redact_words.txt")
    staff_file = Path("school_staff.txt")

    # Load both lists
    words = load_redaction_list(redact_file)
    staff = load_redaction_list(staff_file)

    # Combine them
    all_words = words + staff
    if not all_words:
        print("No words loaded — nothing to redact.")
        return

    re_words = build_word_regex(all_words)
    if re_words is None:
        print("No valid regex could be built — nothing to redact.")
        return

    # Process all target files (skip those that don't exist)
    for p in targets:
        process_txt(p, re_words)

    # --- Optional: Process ANY combined_*.txt in the folder ---
    # for p in sorted(base.glob("combined_*.txt")):
    #     process_txt(p, re_words)

if __name__ == "__main__":
    main()
