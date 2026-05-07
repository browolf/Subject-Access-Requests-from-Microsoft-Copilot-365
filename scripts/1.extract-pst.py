"""
PST Export Message Extractor

This script processes extracted Outlook PST export folders and builds a
filtered evidence set for Subject Access Requests (SARs), investigations,
or eDiscovery review workflows.

Features
--------
- Extracts messages, appointments, and meetings
- Converts HTML message bodies into readable text
- Filters content using a target name
- Preserves metadata including:
    - Subject
    - Date
    - Sender
    - Recipients
- Copies matching attachments
- Handles duplicate filenames safely
- Optionally deletes original export folders after processing

Output Structure
----------------
merged_outputs/
├── 00001_message.txt
├── 00002_message.txt
├── 00001_appointment.txt
├── 00001_meeting.txt
└── attachments/

Each exported text file contains structured headers such as:

================================================================================
Source: ./Example.export/Top of Personal Folders/Items/Message00001/message.txt
Subject: Example Subject
Date: Tue, 18 Mar 2025 09:14:10 +0000
From: Example Sender
To:
  - Example Recipient
================================================================================

Requirements
------------
pip install beautifulsoup4

Usage
-----
Place this script inside the directory containing extracted `.export` folders.

Run:
    python extract.py

The script will prompt for:
    - Name to search for
    - Whether original export folders should be deleted after processing

Matching Logic
--------------
The script performs case-insensitive matching against:
    - Message subjects
    - Message bodies
    - Appointment content
    - Meeting content

Example input:
    john smith

Will match:
    - john
    - smith

Supported Content
-----------------
- Messages
- Meetings
- Appointments
- HTML message bodies
- Attachments containing the target name in the filename

Notes
-----
- HTML files are converted into `.txt` files during processing
- Attachments are copied into a central `attachments` folder
- Duplicate filenames are automatically renamed with numeric suffixes
- Original export folders can optionally be deleted after successful processing

Intended Use
------------
This tool is intended to assist with:
    - Subject Access Requests (SARs)
    - Internal investigations
    - eDiscovery review
    - PST content triage
    - Email evidence preparation

This script provides technical tooling only and does not constitute legal advice.
"""


import os
import shutil
from bs4 import BeautifulSoup

ROOT_DIR = "."
OUTPUT_ROOT = "./merged_outputs"
ATTACHMENTS_DIR = os.path.join(OUTPUT_ROOT, "attachments")

os.makedirs(OUTPUT_ROOT, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

MESSAGE_COUNTER = 1
APPOINTMENT_COUNTER = 1
MEETING_COUNTER = 1


def safe_copy_or_move(src_path, dst_dir, delete_mode):
    os.makedirs(dst_dir, exist_ok=True)
    base = os.path.basename(src_path)
    name, ext = os.path.splitext(base)

    candidate = os.path.join(dst_dir, base)

    if not os.path.exists(candidate):
        if delete_mode:
            shutil.move(src_path, candidate)
        else:
            shutil.copy2(src_path, candidate)
        return candidate

    n = 1
    while True:
        new_name = f"{name}_{n}{ext}"
        candidate = os.path.join(dst_dir, new_name)
        if not os.path.exists(candidate):
            if delete_mode:
                shutil.move(src_path, candidate)
            else:
                shutil.copy2(src_path, candidate)
            return candidate
        n += 1


def contains_name(text, name_parts):
    text_lower = text.lower()
    return any(part in text_lower for part in name_parts)


def convert_html_to_text_simple(root_dir, delete_mode):
    html_exts = {".html", ".htm"}

    for current_root, _, files in os.walk(root_dir):
        for file in files:
            ext = os.path.splitext(file.lower())[1]
            if ext not in html_exts:
                continue

            html_path = os.path.join(current_root, file)
            txt_path = os.path.splitext(html_path)[0] + ".txt"

            try:
                with open(html_path, "r", encoding="utf-8", errors="replace") as f:
                    soup = BeautifulSoup(f.read(), "html.parser")

                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()

                text = soup.get_text(separator="\n", strip=True)
                lines = [line.strip() for line in text.splitlines() if line.strip()]

                merged = []
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if line.endswith(":") and i + 1 < len(lines):
                        nxt = lines[i + 1]
                        if not nxt.endswith(":"):
                            merged.append(f"{line} {nxt}")
                            i += 2
                            continue
                    merged.append(line)
                    i += 1

                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(merged))

                if delete_mode:
                    os.remove(html_path)

            except Exception as e:
                print(f"HTML conversion error: {html_path} -> {e}")


def extract_subject_date(headers_path):
    subject = None
    date = None
    try:
        with open(headers_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                l = line.lower()
                if subject is None and l.startswith("subject:"):
                    subject = line.split(":", 1)[1].strip()
                if date is None and l.startswith("date:"):
                    date = line.split(":", 1)[1].strip()
                if subject and date:
                    break
    except:
        pass
    return subject, date


def extract_sender(headers_path):
    try:
        with open(headers_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.lower().startswith("sender name:"):
                    sender = line.split(":", 1)[1].strip()
                    return sender if sender else "(unknown sender)"
    except:
        pass
    return "(unknown sender)"


def extract_recipients(recipients_path):
    recipients = []
    try:
        with open(recipients_path, "r", encoding="utf-8", errors="replace") as f:
            current_name = ""

            for line in f:
                line = line.strip()
                l = line.lower()

                if l.startswith("display name:"):
                    current_name = line.split(":", 1)[1].strip()

                elif l.startswith("recipient type:"):
                    if current_name:
                        recipients.append(current_name)
                    current_name = ""

            if current_name:
                recipients.append(current_name)

    except:
        pass

    return recipients if recipients else ["(no recipients)"]


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except:
        return ""


def header(source, subject=None, date=None, sender=None, recipients=None):
    h = "\n" + "=" * 80 + "\n"
    h += f"Source: {source}\n"

    if subject is not None:
        h += f"Subject: {subject or '(missing)'}\n"
        h += f"Date: {date or '(missing)'}\n"

    if sender:
        h += f"From: {sender}\n"

    if recipients:
        h += "To:\n"
        for r in recipients:
            h += f"  - {r}\n"

    h += "=" * 80 + "\n\n"
    return h


def write_message(content):
    global MESSAGE_COUNTER
    filename = f"{MESSAGE_COUNTER:05d}_message.txt"
    path = os.path.join(OUTPUT_ROOT, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    MESSAGE_COUNTER += 1


def write_appointment(content):
    global APPOINTMENT_COUNTER
    filename = f"{APPOINTMENT_COUNTER:05d}_appointment.txt"
    path = os.path.join(OUTPUT_ROOT, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    APPOINTMENT_COUNTER += 1


def write_meeting(content):
    global MEETING_COUNTER
    filename = f"{MEETING_COUNTER:05d}_meeting.txt"
    path = os.path.join(OUTPUT_ROOT, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    MEETING_COUNTER += 1


def process_export(folder, name, name_parts, delete_mode):
    # --- Attachments ---
    for root, _, files in os.walk(folder):
        if "attachment" not in root.lower():
            continue

        for file in files:
            if name not in file.lower():
                continue

            path = os.path.join(root, file)
            safe_copy_or_move(path, ATTACHMENTS_DIR, delete_mode)

    # --- Convert HTML ---
    convert_html_to_text_simple(folder, delete_mode)

    messages, appointments, meetings = [], [], []

    for root, _, files in os.walk(folder):
        files_lower = {f.lower(): f for f in files}

        if "message.txt" in files_lower:
            messages.append(os.path.join(root, files_lower["message.txt"]))
        if "appointment.txt" in files_lower:
            appointments.append(os.path.join(root, files_lower["appointment.txt"]))
        if "meeting.txt" in files_lower:
            meetings.append(root)

    # --- Messages ---
    for path in sorted(messages):
        base_dir = os.path.dirname(path)

        subject, date = extract_subject_date(os.path.join(base_dir, "internetheaders.txt"))
        sender = extract_sender(os.path.join(base_dir, "outlookheaders.txt"))
        recipients = extract_recipients(os.path.join(base_dir, "recipients.txt"))

        body = read_text(path).strip()
        combined = f"{subject or ''} {body}"

        if contains_name(combined, name_parts):
            body = body or "no body to this message"
            content = header(path, subject, date, sender, recipients) + body + "\n"
            write_message(content)

    # --- Appointments ---
    for path in sorted(appointments):
        body = read_text(path).strip()

        if contains_name(body, name_parts):
            body = body or "no body to this appointment"
            content = header(path) + body + "\n"
            write_appointment(content)

    # --- Meetings ---
    for root in sorted(meetings):
        meeting = read_text(os.path.join(root, "meeting.txt")).strip()
        message = read_text(os.path.join(root, "message.txt")).strip()
        combined = f"{meeting} {message}"

        if contains_name(combined, name_parts):
            combined_text = "\n\n".join([x for x in [meeting, message] if x]) or "no body to this meeting"
            content = header(root) + combined_text + "\n"
            write_meeting(content)

    print(f"Done: {folder}")

    if delete_mode:
        shutil.rmtree(folder)
        print(f"Deleted folder: {folder}")


def main():
    name = input("Enter the name to keep (firstname surname): ").strip().lower()
    name_parts = [p for p in name.split() if p]

    delete_input = input("Delete original folders after processing? (y/n): ").strip().lower()
    delete_mode = delete_input == "y"

    for folder in os.listdir(ROOT_DIR):
        if folder.endswith(".export"):
            process_export(os.path.join(ROOT_DIR, folder), name, name_parts, delete_mode)


if __name__ == "__main__":
    main()
