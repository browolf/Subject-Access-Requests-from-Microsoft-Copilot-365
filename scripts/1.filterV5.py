"""
================================================================================
filterv5.py
================================================================================

PST Export Cleaner & Merger Tool

This script processes Outlook PST export folders (e.g. output.export) and:
- Filters and retains files related to a specified person (by name match)
- Moves matching attachments into a central /attachments folder
- Deletes irrelevant files and known unnecessary metadata files
- Converts HTML email bodies to clean, readable plain text
- Extracts and formats key email headers (Subject, Date)
- Merges:
    • message.txt files → combined_messages.txt (with Subject/Date)
    • appointment.txt files → combined_appointments.txt
    • meeting.txt (+ optional message.txt) → combined_meetings.txt
- Cleans up empty directories and removes redundant PST structure folders

Key Features:
- Safe file moves with automatic rename collision handling
- Robust HTML → text conversion using BeautifulSoup
- Intelligent header parsing from internetheaders.txt
- Clean output formatting with indexed sections
- Handles missing or empty message bodies gracefully
- Designed for large-scale SAR / eDiscovery workflows

Typical Use Case:
Processing PST exports for Subject Access Requests (SAR), investigations,
or data extraction where only specific individuals' data is required.

Requirements:
- Python 3.x
- beautifulsoup4

Usage:
    python filterv5.py
    → Enter target name (e.g. "firstname surname") when prompted

Output:
- output.export/
    ├── attachments/
    ├── combined_messages.txt
    ├── combined_appointments.txt
    └── combined_meetings.txt

Notes:
- Original HTML files are deleted after conversion
- The "Items" folder is removed after processing
- Only files containing the specified name are preserved

================================================================================
"""

import os
import sys
import shutil
from bs4 import BeautifulSoup


def safe_move(src_path, dst_dir):
    """
    Move src_path into dst_dir. If a file with the same name exists,
    append ' (1)', ' (2)', ... before the extension to avoid overwriting.
    Returns the final destination path.
    """
    os.makedirs(dst_dir, exist_ok=True)
    base = os.path.basename(src_path)
    name, ext = os.path.splitext(base)
    candidate = os.path.join(dst_dir, base)

    if not os.path.exists(candidate):
        shutil.move(src_path, candidate)
        return candidate

    # Resolve collisions by appending (n)
    n = 1
    while True:
        new_name = f"{name} ({n}){ext}"
        candidate = os.path.join(dst_dir, new_name)
        if not os.path.exists(candidate):
            shutil.move(src_path, candidate)
            return candidate
        n += 1


def try_remove_if_empty(dir_path):
    """
    Remove the directory only if it is empty. Returns True if removed, False otherwise.
    """
    try:
        if os.path.isdir(dir_path) and not os.listdir(dir_path):
            os.rmdir(dir_path)
            print(f"Removed empty folder: {dir_path}")
            return True
    except Exception as e:
        print(f"Could not remove '{dir_path}': {e}")
    return False


def convert_html_to_text_simple(root_dir):
    """
    Find .html/.htm files under root_dir, extract text using BeautifulSoup,
    save as .txt in the same folder, and delete the original HTML.
    Assumes only 1 HTML file per folder, so no overwrite protection needed.
    """
    html_exts = {".html", ".htm"}

    for current_root, _, files in os.walk(root_dir):
        for file in files:
            ext = os.path.splitext(file.lower())[1]
            if ext not in html_exts:
                continue

            html_path = os.path.join(current_root, file)
            txt_path = os.path.splitext(html_path)[0] + ".txt"

            # Read HTML
            try:
                with open(html_path, "r", encoding="utf-8", errors="replace") as f:
                    html_content = f.read()
            except Exception as e:
                print(f"Cannot read '{html_path}': {e}")
                continue

            try:
                soup = BeautifulSoup(html_content, "html.parser")

                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()

                text = soup.get_text(separator="\n", strip=True)

                # Clean empty lines
                lines = [line.strip() for line in text.splitlines() if line.strip()]

                # Merge "To:", "From:", "Cc:", etc. with the next line
                merged = []
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if line.endswith(":") and i + 1 < len(lines):
                        next_line = lines[i + 1]
                        # Join only if the next line is not another header
                        if not next_line.endswith(":"):
                            merged.append(f"{line} {next_line}")
                            i += 2
                            continue
                    merged.append(line)
                    i += 1

                cleaned_text = "\n".join(merged)

                # Write .txt
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_text)

                print(f"Converted HTML → {txt_path}")
                try:
                    os.remove(html_path)
                    print(f"Deleted: {html_path}")
                except Exception as e:
                    print(f"Could not delete '{html_path}': {e}")

            except Exception as e:
                print(f"Error converting '{html_path}': {e}")


# -----------------------------
# Helpers for parsing / headers
# -----------------------------

def extract_subject_date(headers_path):
    """
    From internetheaders.txt (same folder), extract first 'Subject:' and 'Date:' lines (case-insensitive).
    Returns (subject or None, date or None).
    """
    subject = None
    date = None
    try:
        with open(headers_path, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                line = raw.strip()
                low = line.lower()
                if subject is None and low.startswith("subject:"):
                    subject = line.split(":", 1)[1].strip() or None
                elif date is None and low.startswith("date:"):
                    date = line.split(":", 1)[1].strip() or None
                if subject and date:
                    break
    except Exception:
        pass
    return subject, date


def read_text_contents(path):
    """
    Read a text file as utf-8 with replacement, return its content as string (may be empty string).
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def header_block(idx, total, source_path_or_dir):
    """
    Builds a standardized section header WITHOUT Subject/Date (for appointments and meetings).
    """
    return (
        "\n" + "=" * 80 + "\n"
        f"[{idx}/{total}] Source: {source_path_or_dir}\n"
        + "=" * 80 + "\n\n"
    )


def header_block_message(idx, total, source_path_or_dir, subject, date):
    """
    Builds a standardized section header WITH Subject/Date (for messages).
    """
    subject_disp = subject if subject else "(missing)"
    date_disp = date if date else "(missing)"
    return (
        "\n" + "=" * 80 + "\n"
        f"[{idx}/{total}] Source: {source_path_or_dir}\n"
        f"Subject: {subject_disp}\n"
        f"Date: {date_disp}\n"
        + "=" * 80 + "\n\n"
    )


# -----------------------------
# Merge routines
# -----------------------------

def merge_message_txts(root_dir, combined_out_path):
    """
    Merge all message.txt files. Header includes Subject/Date from internetheaders.txt.
    Empty body → "no body to this message".
    """
    gathered = []
    for current_root, _, files in os.walk(root_dir):
        if "message.txt" in {f.lower() for f in files}:
            gathered.append(os.path.join(current_root, "message.txt"))

    if not gathered:
        print("No message.txt files found to merge.")
        return

    gathered.sort()

    try:
        os.makedirs(os.path.dirname(combined_out_path), exist_ok=True)
        with open(combined_out_path, "w", encoding="utf-8") as out_f:
            total = len(gathered)
            for i, path in enumerate(gathered, 1):
                folder = os.path.dirname(path)
                headers_path = os.path.join(folder, "internetheaders.txt")
                subject, date = extract_subject_date(headers_path)

                body = read_text_contents(path).strip()
                if not body:
                    body = "no body to this message"

                out_f.write(header_block_message(i, total, path, subject, date))
                out_f.write(body + "\n")
        print(f"Merged {len(gathered)} message.txt files → {combined_out_path}")
    except Exception as e:
        print(f"Failed to write combined file '{combined_out_path}': {e}")


def merge_appointment_txts(root_dir, combined_out_path):
    """
    Merge all appointment.txt files. Header DOES NOT include Subject/Date.
    Empty body → "no body to this appointment".
    """
    gathered = []
    for current_root, _, files in os.walk(root_dir):
        if "appointment.txt" in {f.lower() for f in files}:
            gathered.append(os.path.join(current_root, "appointment.txt"))

    if not gathered:
        print("No appointment.txt files found to merge.")
        return

    gathered.sort()

    try:
        os.makedirs(os.path.dirname(combined_out_path), exist_ok=True)
        with open(combined_out_path, "w", encoding="utf-8") as out_f:
            total = len(gathered)
            for i, path in enumerate(gathered, 1):
                body = read_text_contents(path).strip()
                if not body:
                    body = "no body to this appointment"

                out_f.write(header_block(i, total, path))
                out_f.write(body + "\n")
        print(f"Merged {len(gathered)} appointment.txt files → {combined_out_path}")
    except Exception as e:
        print(f"Failed to write combined file '{combined_out_path}': {e}")


def merge_meeting_and_message_txts(root_dir, combined_out_path):
    """
    For each folder containing meeting.txt (and optional message.txt),
    create one combined entry. Header DOES NOT include Subject/Date.
    Order: meeting body first, then blank line, then message body (if present).
    If both bodies are empty/missing → "no body to this meeting".
    """
    folders = []

    for current_root, _, files in os.walk(root_dir):
        if "meeting.txt" in {f.lower() for f in files}:
            folders.append(current_root)

    if not folders:
        print("No meeting.txt folders found.")
        return

    folders.sort()

    try:
        os.makedirs(os.path.dirname(combined_out_path), exist_ok=True)
        with open(combined_out_path, "w", encoding="utf-8") as out_f:
            total = len(folders)
            for i, folder in enumerate(folders, 1):
                meeting_path = os.path.join(folder, "meeting.txt")
                message_path = os.path.join(folder, "message.txt")

                meeting_body = read_text_contents(meeting_path).strip()
                message_body = read_text_contents(message_path).strip() if os.path.exists(message_path) else ""

                combined_parts = []
                if meeting_body:
                    combined_parts.append(meeting_body)
                if message_body:
                    if combined_parts:
                        combined_parts.append("")  # blank line separator
                    combined_parts.append(message_body)

                combined_body = "\n".join(combined_parts).strip() if combined_parts else ""

                if not combined_body:
                    combined_body = "no body to this meeting"

                out_f.write(header_block(i, total, folder))
                out_f.write(combined_body + "\n")

        print(f"Merged meetings → {combined_out_path}")
    except Exception as e:
        print(f"Failed to write combined file '{combined_out_path}': {e}")


def main():
    name = input("Enter the name to keep (firstname surname): ").strip().lower()

    target_dir = "output.export"
    attachments_dir = os.path.join(target_dir, "attachments")

    # Ensure leading dots for all extensions
    extensions = {".xlsx", ".docx", ".pdf", ".csv", ".doc", ".xls", ".pptx", ".ppt"}

    always_delete_filenames = {"conversationindex.txt", "recipients.txt"}

    if not os.path.isdir(target_dir):
        print(f"Folder '{target_dir}' not found.")
        sys.exit(1)

    for root, _, files in os.walk(target_dir):
        # Skip attachments destination to avoid re-processing moved files
        if os.path.abspath(root) == os.path.abspath(attachments_dir):
            continue

        for file in files:
            file_lower = file.lower()
            base_lower = os.path.basename(file_lower)
            ext = os.path.splitext(file_lower)[1]
            file_path = os.path.join(root, file)

            if base_lower in always_delete_filenames:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                continue

            if ext in extensions:
                if name in file_lower:
                    try:
                        final_dest = safe_move(file_path, attachments_dir)
                        print(f"Kept & moved: {final_dest}")
                    except Exception as e:
                        print(f"Failed to move '{file_path}': {e}")
                else:
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass

    # Remove empty folders (only if empty)
    try_remove_if_empty(os.path.join(target_dir, "Search Root"))
    try_remove_if_empty(os.path.join(target_dir, "SPAM Search Folder 2"))
    try_remove_if_empty(
        os.path.join(target_dir, "Top of Personal Folders", "Deleted Items")
    )

    # Convert HTML → txt
    convert_html_to_text_simple(target_dir)

    # Merge message.txt → output.export/combined_messages.txt (Subject/Date from internetheaders.txt)
    combined_messages_path = os.path.join(target_dir, "combined_messages.txt")
    merge_message_txts(target_dir, combined_messages_path)

    # Merge appointment.txt → output.export/combined_appointments.txt (NO Subject/Date in header)
    combined_appt_path = os.path.join(target_dir, "combined_appointments.txt")
    merge_appointment_txts(root_dir=target_dir, combined_out_path=combined_appt_path)

    # Merge meeting.txt (+ optional message.txt) → output.export/combined_meetings.txt (NO Subject/Date in header)
    combined_meetings_path = os.path.join(target_dir, "combined_meetings.txt")
    merge_meeting_and_message_txts(target_dir, combined_meetings_path)

    # DELETE the entire Items folder: output.export/Top of Personal Folders/Items
    items_dir = os.path.join(target_dir, "Top of Personal Folders", "Items")
    shutil.rmtree(items_dir, ignore_errors=True)
    print(f"Removed folder (if existed): {items_dir}")


if __name__ == "__main__":
    main()
