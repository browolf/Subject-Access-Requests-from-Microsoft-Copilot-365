"""
Merged Export Consolidation Tool

This script merges extracted message, appointment, and meeting files
from the `merged_outputs` folder into separate consolidated text files.

During processing, selected header information is removed to help
produce cleaner review datasets suitable for searching, disclosure,
or further redaction workflows.

Features
--------
- Merges exported files into combined output documents
- Separates:
    - Messages
    - Appointments
    - Meetings
- Cleans selected header metadata
- Preserves message structure and separators
- Processes files in sorted order
- Outputs dedicated merged files by content type

Input Folder
------------
Expected input folder:

./merged_outputs/

Example files:
    00001_message.txt
    00002_message.txt
    00001_appointment.txt
    00001_meeting.txt

Output Files
------------
Generated output files:

    ./merged_messages.txt
    ./merged_appointments.txt
    ./merged_meetings.txt

Header Cleaning
---------------
The script removes the following header fields:

    Source:
    From:

It also removes recipient sections:

    To:
      - Example Recipient
      - Another Recipient

Remaining headers such as:
    Subject:
    Date:

are preserved.

Example
-------
Original:

================================================================================
Source: ./Example.export/Message00001/message.txt
Subject: Example Subject
Date: Tue, 18 Mar 2025 09:14:10 +0000
From: John Smith
To:
  - Jane Doe
  - Example User
================================================================================

Processed:

================================================================================
Subject: Example Subject
Date: Tue, 18 Mar 2025 09:14:10 +0000
================================================================================

Processing Logic
----------------
Files are categorised by filename suffix:

    *_message.txt
    *_appointment.txt
    *_meeting.txt

Each type is written into its corresponding merged output file.

Usage
-----
Run:
    python merge_exports.py

The script will:
    - Scan `merged_outputs`
    - Categorise files by type
    - Remove selected header fields
    - Merge content into consolidated files

Example Output
--------------
Done. Outputs written:

message: ./merged_messages.txt
appointment: ./merged_appointments.txt
meeting: ./merged_meetings.txt

Notes
-----
- Existing output files are overwritten
- Files are processed in alphabetical order
- Only recognised file types are included
- Errors reading individual files are displayed but processing continues
- Message separators are preserved
- Header cleaning only affects:
      Source:
      From:
      To:
  sections

Technical Details
-----------------
The script:
    - Opens all output files once at startup
    - Streams merged content sequentially
    - Uses filename suffix matching for categorisation

Supported suffixes:
    _message.txt
    _appointment.txt
    _meeting.txt

Intended Use
------------
This tool is intended to assist with:
    - Subject Access Request (SAR) preparation
    - Email dataset consolidation
    - eDiscovery workflows
    - Internal investigations
    - Redaction preprocessing

This script provides technical tooling only and does not constitute legal advice.
"""


import os

INPUT_DIR = "./merged_outputs"

OUTPUT_FILES = {
    "message": "./merged_messages.txt",
    "appointment": "./merged_appointments.txt",
    "meeting": "./merged_meetings.txt"
}


def clean_header(block):
    lines = block.splitlines()
    cleaned = []

    skip_to_section = False

    for line in lines:
        l = line.strip().lower()

        # remove Source and From
        if l.startswith("source:") or l.startswith("from:"):
            continue

        # start skipping To section
        if l.startswith("to:"):
            skip_to_section = True
            continue

        # skip recipient lines (e.g. "  - John Smith")
        if skip_to_section:
            if line.startswith("="):  # end of header
                skip_to_section = False
                cleaned.append(line)
            elif line.strip().startswith("-"):
                continue
            else:
                skip_to_section = False

        cleaned.append(line)

    return "\n".join(cleaned)


def get_type(filename):
    name = filename.lower()
    if name.endswith("_message.txt"):
        return "message"
    elif name.endswith("_appointment.txt"):
        return "appointment"
    elif name.endswith("_meeting.txt"):
        return "meeting"
    return None


def main():
    files = sorted(os.listdir(INPUT_DIR))

    # open all output files once
    outputs = {}
    for t, path in OUTPUT_FILES.items():
        outputs[t] = open(path, "w", encoding="utf-8")

    for file in files:
        file_type = get_type(file)
        if not file_type:
            continue

        path = os.path.join(INPUT_DIR, file)

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()

            cleaned = clean_header(content)

            outputs[file_type].write(cleaned)
            outputs[file_type].write("\n\n")

        except Exception as e:
            print(f"Error reading {file}: {e}")

    # close all files
    for f in outputs.values():
        f.close()

    print("Done. Outputs written:")
    for t, path in OUTPUT_FILES.items():
        print(f"{t}: {path}")


if __name__ == "__main__":
    main()
