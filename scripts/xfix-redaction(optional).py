"""
Interactive Word Replacement / Unredaction Tool

This script scans exported message files inside the `merged_outputs`
folder and allows the reviewer to interactively replace specific words
or phrases with custom replacement text.

The primary intended use is correcting redaction mistakes where content
was incorrectly replaced with:

    <redacted>

The reviewer can selectively restore words, names, or phrases by
replacing incorrect redactions with the desired text.

The script preserves message headers and modifies only the message body.

Features
--------
- Interactive terminal workflow
- Custom replacement text
- Designed for correcting redaction mistakes
- Processes all `_message.txt` files
- Preserves message headers
- Replaces content only within message bodies
- Displays per-file replacement counts
- Supports repeated replacement sessions
- Case-insensitive matching
- Boundary-aware replacement logic

Folder Structure
----------------
Expected input folder:

./merged_outputs/

Example files:
    00001_message.txt
    00002_message.txt

Message Structure
-----------------
The script expects messages to contain separator lines using:

    ================================================================================
    
Messages are split into:
    - Header section
    - Body section

Only the body section is modified.

Typical Usage
--------------
This tool is mainly intended for situations where automated redaction
incorrectly removed content.

Example:

    <redacted>int meeting

Could be corrected back to:

    joint meeting

Or:

    ma<redacted>rity

Could be corrected back to:

    majority

Replacement Behaviour
---------------------
The reviewer enters:
    - A word or phrase to search for
    - A replacement value

Example:

    Enter word to replace: <redacted>int
    Replace '<redacted>int' with: joint

Matching is:
    - Case-insensitive
    - Boundary-aware

Usage
-----
Run:
    python interactive_unredact.py

The script will prompt:

    Enter word to replace (or 'q' to quit):

Then:

    Replace 'word' with:

Example session:

    Enter word to replace (or 'q' to quit): <redacted>int
    Replace '<redacted>int' with: joint

    Replaced 4 occurrence(s) of '<redacted>int'

    Enter word to replace (or 'q' to quit): ma<redacted>rity
    Replace 'ma<redacted>rity' with: majority

    Replaced 2 occurrence(s) of 'ma<redacted>rity'

    Enter word to replace (or 'q' to quit): q

Processing Behaviour
--------------------
For each entered word:
    - All `_message.txt` files are processed
    - Matching words are replaced
    - Files are modified in place
    - Replacement totals are displayed

Example progress output:

    [12/145] 00012_message.txt -> 3

Meaning:
    - File 12 of 145
    - 3 replacements in that file

Technical Details
-----------------
Matching uses the regex pattern:

    (?<![A-Za-z0-9])WORD(?![A-Za-z0-9])

With:
    - re.IGNORECASE

This provides:
    - Case-insensitive matching
    - Boundary-aware replacement behaviour

The script uses `re.subn()` to:
    - Perform replacements
    - Return replacement counts

Notes
-----
- Files are modified in place
- Original files are overwritten
- Headers remain unchanged
- Only files ending in `_message.txt` are processed
- Empty input is ignored
- Typing:
      q
      quit
      exit
  ends the session
- Replacement text is inserted exactly as entered

Limitations
-----------
- Matching is boundary-aware and may not match partial words in all cases
- Replacement text itself is not validated
- Care should be taken to avoid restoring genuinely sensitive information

Intended Use
------------
This tool is intended to assist with:
    - Correcting over-redaction
    - Manual unredaction
    - Subject Access Request (SAR) review
    - Email dataset cleanup
    - eDiscovery review
    - Internal investigations

This script provides technical tooling only and does not constitute legal advice.
"""

import os
import re

FOLDER = "./merged_outputs"
STAFF_FILE = "school_staff.txt"


# =========================
# SPLIT HEADER / BODY
# =========================

def split_header_body(text):
    parts = text.split("=" * 80)

    if len(parts) >= 3:
        header = parts[0] + "=" * 80 + parts[1] + "=" * 80 + "\n\n"
        body = ("=" * 80).join(parts[2:])
        return header, body

    return "", text


# =========================
# REPLACEMENT
# =========================

def replace_word(text, word, replacement):
    pattern = re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])",
        re.IGNORECASE
    )

    new_text, count = pattern.subn(replacement, text)
    return new_text, count


def process_file(path, word, replacement):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content = content.replace("\r\n", "\n")

        header, body = split_header_body(content)

        new_body, count = replace_word(body, word, replacement)

        if count > 0:
            with open(path, "w", encoding="utf-8") as f:
                f.write(header + new_body)

        return count

    except Exception as e:
        print(f"Error: {path} -> {e}")
        return 0


# =========================
# MAIN
# =========================

def main():
    files = []
    for f in os.listdir(FOLDER):
        full_path = os.path.join(FOLDER, f)
        if os.path.isfile(full_path) and f.endswith("_message.txt"):
            files.append(f)

    total_files = len(files)
    print(f"{total_files} message files found.\n")

    while True:
        word = input("Enter word to replace (or 'q' to quit): ").strip()

        if word.lower() in ("q", "quit", "exit"):
            break

        if not word:
            continue

        replacement = input(f"Replace '{word}' with: ")

        total_replaced = 0

        for i, file in enumerate(files, 1):
            path = os.path.normpath(os.path.join(FOLDER, file))

            count = process_file(path, word, replacement)
            total_replaced += count

            print(f"[{i}/{total_files}] {file} -> {count}", end="\r")

        print(f"\nReplaced {total_replaced} occurrence(s) of '{word}'\n")

    print("Done.")


if __name__ == "__main__":
    main()



