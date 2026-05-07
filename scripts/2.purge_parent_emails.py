"""
Message Header Filter

This script scans extracted message files inside the `merged_outputs`
folder and deletes messages where a specified name appears within the
email header sections.

The check is limited to:
    - From:
    - To:

This is useful for removing messages involving particular individuals
from an exported review set before further processing or disclosure.

These messages are removed as requesters need not receive messages they
themselves sent or received. 

Features
--------
- Scans all `_message.txt` files
- Extracts sender and recipient header sections
- Performs case-insensitive matching
- Deletes matching files automatically
- Displays deletion statistics when complete

Folder Structure
----------------
Expected input folder:

./merged_outputs/

Example files:
    00001_message.txt
    00002_message.txt
    00003_message.txt

Matching Logic
--------------
The supplied name is split into parts and matched individually.

Example input:
    john smith

Will match:
    - john
    - smith

The script searches only within:
    From:
    To:

It does NOT search:
    - Subject lines
    - Message body content
    - Attachments

Example Header
--------------
================================================================================
From: John Smith
To:
  - Jane Doe
  - Example User
================================================================================

Usage
-----
Run:
    python filter_headers.py

The script will prompt:

    Enter name (it will look for the name in the headers)):

Example:
    john smith

Output
------
Matching files are deleted immediately.

Final statistics are displayed:

    Done. Deleted X of Y message files.

Notes
-----
- Matching is case-insensitive
- Only files ending in `_message.txt` are processed
- Files are permanently deleted using `os.remove()`
- Errors reading individual files are displayed but do not stop processing

Intended Use
------------
This script is intended to assist with:
    - Subject Access Request (SAR) preparation
    - Email dataset filtering
    - Internal investigations
    - eDiscovery review workflows

This script provides technical tooling only and does not constitute legal advice.
"""


import os

FOLDER = "./merged_outputs"


def extract_header_sections(content):
    lines = content.splitlines()

    from_line = ""
    to_lines = []
    in_to_section = False

    for line in lines:
        l = line.lower().strip()

        if l.startswith("from:"):
            from_line = line

        elif l.startswith("to:"):
            in_to_section = True
            continue

        elif in_to_section:
            if line.startswith("="):  # end of header
                break
            if line.strip().startswith("-"):
                to_lines.append(line)

    return from_line, to_lines


def should_delete(content, name_parts):
    from_line, to_lines = extract_header_sections(content)

    combined = " ".join([from_line] + to_lines).lower()

    return any(part in combined for part in name_parts)


def main():
    name = input("Enter name (it will look for the name in the headers)): ").strip().lower()
    name_parts = [p for p in name.split() if p]

    deleted = 0
    total = 0

    for file in os.listdir(FOLDER):
        if not file.endswith("_message.txt"):
            continue

        total += 1
        path = os.path.join(FOLDER, file)

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            if should_delete(content, name_parts):
                os.remove(path)
                deleted += 1

        except Exception as e:
            print(f"Error processing {file}: {e}")

    print(f"\nDone. Deleted {deleted} of {total} message files.")


if __name__ == "__main__":
    main()
