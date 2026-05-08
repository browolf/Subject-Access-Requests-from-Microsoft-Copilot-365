"""
Manual Redaction Tool

Interactive Python script for manually redacting words inside
merged_messages.txt.

Features
--------
- Searches the entire file including:
    - Subjects
    - Dates
    - Headers
    - Message bodies
- Case-insensitive matching
- Whole-word matching only
- Displays replacement counts per line
- Interactive command-line workflow
- Supports repeated redaction operations in one session

Usage
-----
python redact_manual.py

Example
-------
Enter word to redact (or 'q' to quit): Smith
[12/842] -> 2
[19/842] -> 1

Replaced 3 occurrence(s) of 'Smith'

Notes
-----
- Uses whole-word matching to reduce accidental partial replacements
- Matching is case-insensitive
- Current version only processes data in memory and does not save
  changes back to the file

Input File
----------
merged_messages.txt

Replacement Format
------------------
<redacted>

Requirements
------------
- Python 3.x
- No external dependencies required
"""


import os
import re

INPUT_FILE = "merged_messages.txt"


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

    while True:
        word = input("Enter word to redact (or 'q' to quit): ").strip()

        if word.lower() in ("q", "quit", "exit"):
            break

        if not word:
            continue

        total_replaced = 0
        new_lines = []

        for i, line in enumerate(lines, 1):

            # SEARCH EVERY LINE INCLUDING HEADERS
            new_line, count = replace_word_in_line(line, word)

            total_replaced += count
            new_lines.append(new_line)

            if count > 0:
                print(f"[{i}/{len(lines)}] -> {count}")

        lines = new_lines

        print(f"\nReplaced {total_replaced} occurrence(s) of '{word}'\n")

    print("Done.")


if __name__ == "__main__":
    main()
