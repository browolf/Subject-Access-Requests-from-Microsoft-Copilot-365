"""
Email and Staff Name Redaction Tool

This script scans exported message files inside the `merged_outputs`
folder and redacts:
    - Email addresses
    - Staff names

The script is intended to assist with preparing email datasets for
review or disclosure by sanitising message body content while preserving
message headers.

Features
--------
- Processes all `_message.txt` files
- Redacts email addresses
- Supports exempt email addresses
- Redacts staff names from a configurable list
- Preserves message headers
- Modifies only the message body
- Displays per-file replacement statistics
- Outputs overall processing totals

Configuration Files
-------------------
Email exemptions are loaded from:

    exemptions.json

Example:

{
    "emails": [
        "headteacher@school.org",
        "admin@school.org"
    ]
}

Staff names are loaded from:

    school_staff.txt

Example:

    John Smith
    Jane Doe
    Example User

One name per line.

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

Redaction Behaviour
-------------------
Email addresses are replaced with:

    <redacted>

Unless the email address exists in `exemptions.json`.

Supported email formats include:

    john@example.com
    <john@example.com>

Staff names are also replaced with:

    <redacted>

Matching is case-insensitive.

Example:
    John Smith  ->  <redacted>

Headers are preserved and are NOT modified.

Usage
-----
Run:
    python redact_content.py

The script will:
    - Load exempt email addresses
    - Load staff names
    - Process all `_message.txt` files
    - Redact matching content
    - Save modified files in place

Example Output
--------------
Processing 120 files...

00014_message.txt
  emails: 3
  names:  4

00027_message.txt
  emails: 1
  names:  2

Done.
Files processed: 120
Total changes:   43

Technical Details
-----------------
Email matching uses the regex:

    <?([\\w\\.-]+@[\\w\\.-]+\\.\\w+)>?

This supports:
    - Standard email addresses
    - Angle-bracketed email addresses

Staff name matching uses:
    - re.IGNORECASE
    - Custom boundary-aware regex checks

Boundary pattern:

    (?<![A-Za-z0-9])NAME(?![A-Za-z0-9])

This helps prevent accidental redaction inside larger words.

Notes
-----
- Files are modified in place
- Original files are overwritten
- Headers remain unchanged
- Only files ending in `_message.txt` are processed
- Empty lines in `school_staff.txt` are ignored
- Exempt email addresses are matched case-insensitively
- Errors reading individual files are displayed but processing continues

Intended Use
------------
This tool is intended to assist with:
    - Subject Access Request (SAR) preparation
    - Email redaction workflows
    - eDiscovery review
    - Internal investigations
    - Dataset sanitisation

This script provides technical tooling only and does not constitute legal advice.
"""


import os
import re
import json

FOLDER = "./merged_outputs"
EXEMPTIONS_FILE = "exemptions.json"
STAFF_FILE = "school_staff.txt"


# =========================
# LOAD DATA
# =========================

def load_exempt_emails():
    with open(EXEMPTIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(e.lower() for e in data.get("emails", []))


def load_staff_names():
    with open(STAFF_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


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
# REDACTION FUNCTIONS
# =========================

def redact_emails(text, exempt_emails):
    count = 0
    pattern = re.compile(r"<?([\w\.-]+@[\w\.-]+\.\w+)>?")

    def replace(match):
        nonlocal count
        email = match.group(1)

        if email.lower() in exempt_emails:
            return match.group(0)

        count += 1
        return "<redacted>"

    return pattern.sub(replace, text), count


def redact_names(text, names):
    total = 0

    for name in names:
        pattern = re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])",
            re.IGNORECASE
        )

        matches = len(pattern.findall(text))
        total += matches

        text = pattern.sub("<redacted>", text)

    return text, total


# =========================
# PROCESS FILE
# =========================

def process_file(path, exempt_emails, staff_names):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content = content.replace("\r\n", "\n")

        header, body = split_header_body(content)

        body, c1 = redact_emails(body, exempt_emails)
        body, c2 = redact_names(body, staff_names)

        total = c1 + c2

        if total > 0:
            with open(path, "w", encoding="utf-8") as f:
                f.write(header + body)

        return total, c1, c2

    except Exception as e:
        print(f"\nError: {path} -> {e}")
        return 0, 0, 0


# =========================
# MAIN
# =========================

def main():
    exempt_emails = load_exempt_emails()
    staff_names = load_staff_names()

    files = [f for f in os.listdir(FOLDER) if f.endswith("_message.txt")]
    total_files = len(files)

    print(f"Processing {total_files} files...\n")

    total_changes = 0

    for i, file in enumerate(files, 1):
        path = os.path.join(FOLDER, file)

        changes, emails, names = process_file(
            path,
            exempt_emails,
            staff_names
        )

        total_changes += changes

        print(f"[{i}/{total_files}] {file} -> {changes} changes", end="\r")

        if changes > 0:
            print(f"\n{file}")
            print(f"  emails: {emails}")
            print(f"  names:  {names}")

    print("\n\nDone.")
    print(f"Files processed: {total_files}")
    print(f"Total changes:   {total_changes}")


if __name__ == "__main__":
    main()
