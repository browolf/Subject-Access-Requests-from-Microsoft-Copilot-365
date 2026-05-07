"""
Merged Message Interactive Redaction Tool (Optional)

This script performs interactive word redaction against the consolidated
message dataset stored in:

    merged_messages_redacted.txt

The reviewer can repeatedly enter words or names to redact from the
message content. Matching words are replaced with:

    <redacted>

The script preserves structural metadata by skipping:
    - Subject lines
    - Date lines
    - Divider lines

It also supports automatically appending reviewed words to
`school_staff.txt` for future reuse.

Features
--------
- Interactive terminal workflow
- Redacts user-supplied words or names
- Processes a single merged message dataset
- Preserves:
    - Subject lines
    - Date lines
    - Divider separators
- Displays per-line replacement counts
- Saves changes back to the same file
- Automatically appends used words to `school_staff.txt`

Input File
----------
Expected input file:

    merged_messages_redacted.txt

If the file does not exist, processing stops.

Configuration File
------------------
Staff word storage file:

    school_staff.txt

Entered words are appended automatically unless already present.

Example contents:

    John Smith
    Jane Doe

Message Structure
-----------------
The script preserves:
    Subject:
    Date:
    ================================================================================
    
Only normal content lines are modified.

Redaction Behaviour
-------------------
Entered words are replaced with:

    <redacted>

Matching is:
    - Case-insensitive
    - Boundary-aware

Example:
    anne

Will redact:
    Anne
    ANNE

But attempts to avoid unintended matches inside larger words such as:
    annes

Usage
-----
Run:
    python redact_merged_messages.py

The script will display:

    Enter word to redact (or 'q' to quit):

Example session:

    Enter word to redact (or 'q' to quit): john
    Replaced 14 occurrence(s) of 'john'

    Enter word to redact (or 'q' to quit): smith
    Replaced 6 occurrence(s) of 'smith'

    Enter word to redact (or 'q' to quit): q

Processing Behaviour
--------------------
For each entered word:
    - Every line is processed
    - Header and divider lines are skipped
    - Matching words are replaced
    - Replacement counts are displayed

Example progress output:

    [145/3200] -> 2

Meaning:
    - Line 145 of 3200
    - 2 replacements on that line

Technical Details
-----------------
Word matching uses:

    (?<![A-Za-z0-9])WORD(?![A-Za-z0-9])

With:
    - re.IGNORECASE

This provides:
    - Case-insensitive matching
    - Boundary-aware replacement behaviour

The script uses `re.subn()` to:
    - Perform replacements
    - Return replacement counts

Header Detection
----------------
The following lines are preserved:

    Subject:
    Date:

Divider detection:
    Lines consisting entirely of '=' characters

Notes
-----
- The input file is modified in place
- Original content is overwritten
- Empty input is ignored
- Typing:
      q
      quit
      exit
  ends the session
- Words are appended to `school_staff.txt`
- Duplicate entries are avoided automatically
- Errors are minimal because processing occurs entirely in memory

Intended Use
------------
This tool is intended to assist with:
    - Subject Access Request (SAR) preparation
    - Manual redaction workflows
    - Email dataset sanitisation
    - eDiscovery review
    - Internal investigations

This script provides technical tooling only and does not constitute legal advice.
"""


import os
import re

INPUT_FILE = "merged_messages_redacted.txt"
STAFF_FILE = "school_staff.txt"


# =========================
# REDACTION
# =========================

def replace_word_in_line(line, word):
    pattern = re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])",
        re.IGNORECASE
    )
    new_line, count = pattern.subn("<redacted>", line)
    return new_line, count


def is_header_line(line):
    l = line.strip().lower()
    return l.startswith(("subject:", "date:"))


def is_divider_line(line):
    stripped = line.strip()
    return stripped and all(c == "=" for c in stripped)


# =========================
# SAVE WORDS
# =========================

def append_to_staff_file(words):
    existing = set()

    if os.path.exists(STAFF_FILE):
        with open(STAFF_FILE, "r", encoding="utf-8") as f:
            existing = set(line.strip().lower() for line in f if line.strip())

    new_words = [w for w in words if w.lower() not in existing]

    if new_words:
        with open(STAFF_FILE, "a", encoding="utf-8") as f:
            for w in new_words:
                f.write(w + "\n")

        print(f"Appended {len(new_words)} new word(s) to {STAFF_FILE}")
    else:
        print("No new words to append.")


# =========================
# MAIN
# =========================

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"{INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    print(f"{len(lines)} lines loaded.\n")

    used_words = []

    while True:
        word = input("Enter word to redact (or 'q' to quit): ").strip()

        if word.lower() in ("q", "quit", "exit"):
            break

        if not word:
            continue

        used_words.append(word)

        total_replaced = 0
        new_lines = []

        for i, line in enumerate(lines, 1):

            # skip headers + dividers
            if is_header_line(line) or is_divider_line(line):
                new_lines.append(line)
                continue

            new_line, count = replace_word_in_line(line, word)
            total_replaced += count
            new_lines.append(new_line)

            if count > 0:
                print(f"[{i}/{len(lines)}] -> {count}")

        lines = new_lines

        print(f"\nReplaced {total_replaced} occurrence(s) of '{word}'\n")

    # write back
    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    # append words
    if used_words:
        append_to_staff_file(used_words)

    print("Done.")


if __name__ == "__main__":
    main()
