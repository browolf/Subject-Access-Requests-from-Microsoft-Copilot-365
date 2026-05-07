"""
Interactive Word Redaction Tool

This script scans exported message files inside the `merged_outputs`
folder and allows the reviewer to interactively redact specific words
or names from message body content.

Each entered word is replaced with:

    <redacted>

The script is designed for manual cleanup and targeted redaction of
exported email datasets.

Features
--------
- Interactive terminal workflow
- Redacts user-supplied words or names
- Processes all `_message.txt` files
- Preserves message headers
- Redacts only message body content
- Displays per-file replacement counts
- Supports repeated redaction sessions
- Optional support for appending reviewed names to `school_staff.txt`

Folder Structure
----------------
Expected input folder:

./merged_outputs/

Example files:
    00001_message.txt
    00002_message.txt

Configuration File
------------------
Optional staff word storage file:

    school_staff.txt

The script contains functionality to append entered words to this file,
although this feature is currently disabled in the main workflow.

Message Structure
-----------------
The script expects messages to contain separator lines using:

    ================================================================================
    
Messages are split into:
    - Header section
    - Body section

Only the body section is modified.

Redaction Behaviour
-------------------
Entered words are replaced with:

    <redacted>

Matching is:
    - Case-insensitive
    - Boundary-aware

Example:
    john

Will redact:
    john
    John
    JOHN

But attempts to avoid unintended replacements inside larger words.

Example:
    anne

Should not match:
    annes

Usage
-----
Run:
    python interactive_redact.py

The script will display:

    Enter word to redact (or 'q' to quit):

Example session:

    Enter word to redact (or 'q' to quit): john
    Replaced 14 occurrence(s) of 'john'

    Enter word to redact (or 'q' to quit): smith
    Replaced 6 occurrence(s) of 'smith'

    Enter word to redact (or 'q' to quit): q

Output
------
For each entered word:
    - All `_message.txt` files are processed
    - Matching words are replaced
    - Files are modified in place
    - Replacement totals are displayed

Technical Details
-----------------
Word matching uses the regex pattern:

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
- Errors reading individual files are displayed but processing continues

Optional Staff File Integration
-------------------------------
The script contains functionality to append entered words to:

    school_staff.txt

However, this feature is currently disabled via commented-out code:

    #if used_words:
    #    append_to_staff_file(used_words)

Intended Use
------------
This tool is intended to assist with:
    - Subject Access Request (SAR) preparation
    - Manual redaction workflows
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
# REDACTION
# =========================

def replace_word(text, word):
    pattern = re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])",
        re.IGNORECASE
    )

    new_text, count = pattern.subn("<redacted>", text)
    return new_text, count



def process_file(path, word):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content = content.replace("\r\n", "\n")

        header, body = split_header_body(content)

        new_body, count = replace_word(body, word)

        if count > 0:
            with open(path, "w", encoding="utf-8") as f:
                f.write(header + new_body)

        return count

    except Exception as e:
        print(f"Error: {path} -> {e}")
        return 0


# =========================
# SAVE WORDS
# =========================

def append_to_staff_file(words):
    existing = set()

    # load existing names
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
    files = []
    for f in os.listdir(FOLDER):
        full_path = os.path.join(FOLDER, f)
        if os.path.isfile(full_path) and f.endswith("_message.txt"):
            files.append(f)
    total_files = len(files)

    print(f"{total_files} message files found.\n")

    used_words = []

    while True:
        word = input("Enter word to redact (or 'q' to quit): ").strip()

        if word.lower() in ("q", "quit", "exit"):
            break

        if not word:
            continue

        used_words.append(word)

        total_replaced = 0

        for i, file in enumerate(files, 1):
            path = os.path.normpath(os.path.join(FOLDER, file))

            count = process_file(path, word)
            total_replaced += count

            print(f"[{i}/{total_files}] {file} -> {count}", end="\r")

        print(f"\nReplaced {total_replaced} occurrence(s) of '{word}'\n")

    # append words to staff file
    #if used_words:
        #append_to_staff_file(used_words)

    print("Done.")


if __name__ == "__main__":
    main()
