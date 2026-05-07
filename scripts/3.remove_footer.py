"""
Email Footer Removal Tool

This script scans message files inside the `merged_outputs` folder and
removes unwanted email footer blocks using configurable regular expression
patterns stored in a JSON configuration file.

The tool is designed to reduce clutter in exported email datasets by
removing repetitive signatures, disclaimers, confidentiality notices,
external email warnings, and other standard footer content.

Features
--------
- Processes all `_message.txt` files
- Uses configurable regex-based footer patterns
- Preserves message headers
- Removes footer blocks only from the message body
- Supports multiline footer matching
- Displays per-file removal statistics
- Outputs summary statistics when complete

Configuration
-------------
Patterns are loaded from:

    3.footers.json

Example structure:

{
    "remove_blocks": [
        "EXTERNAL EMAIL.*?inspection\\.",
        "This email and any attachments.*?intended recipient\\."
    ]
}

Each entry should be a valid Python regular expression.

Folder Structure
----------------
Expected input:

./merged_outputs/

Example files:
    00001_message.txt
    00002_message.txt

Message Structure
-----------------
The script expects messages to contain separator lines using:

    ================================================================================
    
The message is split into:
    - Header section
    - Body section

Only the body section is modified.

Replacement Text
----------------
Matched footer blocks are replaced with:

    [email footer removed]

Usage
-----
Run:
    python remove_footers.py

The script will:
    - Load regex patterns from `3.footers.json`
    - Scan all `_message.txt` files
    - Remove matching footer blocks
    - Save modified files in place

Example Output
--------------
Processing 120 files...

00014_message.txt -> 2 footer(s) removed
00027_message.txt -> 1 footer(s) removed

Done.
Files processed: 120
Total footers removed: 43

Regex Behaviour
----------------
Patterns are applied using:
    - re.IGNORECASE
    - re.DOTALL

This allows:
    - Case-insensitive matching
    - Matching across multiple lines

Notes
-----
- Files are modified in place
- Original files are overwritten
- Only files ending in `_message.txt` are processed
- If no footer patterns are configured, processing stops
- Invalid regex patterns may cause processing errors
- Headers remain unchanged

Intended Use
------------
This tool is intended to assist with:
    - Subject Access Request (SAR) preparation
    - Email dataset cleanup
    - eDiscovery workflows
    - Internal investigations
    - Reducing repetitive disclaimer noise in exported emails

This script provides technical tooling only and does not constitute legal advice.
"""

import os
import re
import json

FOLDER = "./merged_outputs"
CONFIG_FILE = "3.footers.json"

REPLACEMENT = "[email footer removed]"


# =========================
# LOAD PATTERNS
# =========================

def load_patterns():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("remove_blocks", [])
    except Exception as e:
        print(f"Error loading config: {e}")
        return []


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
# PROCESS FILE
# =========================

def process_file(path, patterns):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content = content.replace("\r\n", "\n")

        header, body = split_header_body(content)

        total_count = 0

        for pattern in patterns:
            matches = re.findall(pattern, body, flags=re.IGNORECASE | re.DOTALL)
            count = len(matches)

            if count > 0:
                body = re.sub(
                    pattern,
                    REPLACEMENT,
                    body,
                    flags=re.IGNORECASE | re.DOTALL
                )
                total_count += count

        if total_count > 0:
            with open(path, "w", encoding="utf-8") as f:
                f.write(header + body)

        return total_count

    except Exception as e:
        print(f"\nError: {path} -> {e}")
        return 0


# =========================
# MAIN
# =========================

def main():
    patterns = load_patterns()

    if not patterns:
        print("No patterns found in config.")
        return

    files = [f for f in os.listdir(FOLDER) if f.endswith("_message.txt")]
    total_files = len(files)

    print(f"Processing {total_files} files...\n")

    total_removed = 0

    for i, file in enumerate(files, 1):
        path = os.path.join(FOLDER, file)

        count = process_file(path, patterns)
        total_removed += count

        print(f"[{i}/{total_files}] {file} -> {count} blocks", end="\r")

        if count > 0:
            print(f"\n{file} -> {count} footer(s) removed")

    print("\n\nDone.")
    print(f"Files processed: {total_files}")
    print(f"Total footers removed: {total_removed}")


if __name__ == "__main__":
    main()
