"""
Interactive Message Review Tool

This script provides a terminal-based review interface for manually
processing exported message files inside the `merged_outputs` folder.

Each message file is displayed individually, allowing the reviewer to:
    - Keep the file
    - Delete the file
    - Quit the session

When deleting a message, the script can optionally delete all other
messages sharing the same subject line.

The tool is designed to support rapid manual review and cleanup of
large exported email datasets.

Features
--------
- Full-screen terminal review workflow
- One-key controls (no Enter required)
- Displays message contents before action
- Supports:
    - Keep
    - Delete
    - Quit
- Optional bulk deletion by matching subject
- Automatic screen clearing between files
- Cross-platform keypress handling:
    - Windows
    - Linux
    - macOS

Folder Structure
----------------
Expected input folder:

./merged_outputs/

Example files:
    00001_message.txt
    00002_message.txt
    00003_appointment.txt

Controls
--------
During review:

    [k] keep
    [d] delete
    [q] quit

No Enter key is required.

Delete by Subject
-----------------
When a file is deleted, the script attempts to extract the subject line
from line 4 of the file.

Example:

    Subject: Re: Meeting Update

The reviewer is then prompted:

    Delete all messages with this subject? (y/n)

If confirmed, all files with the same extracted subject are deleted.

Display Format
--------------
Each file is shown with:

================================================================================
FILE: 00001_message.txt
================================================================================

<message content>

Matching Logic
--------------
Subject matching is:
    - Case-insensitive
    - Exact text comparison after removing "Subject:"

Usage
-----
Run:
    python review_messages.py

The script will:
    - Load all `.txt` files from `merged_outputs`
    - Display them one at a time
    - Wait for reviewer input

Behaviour
---------
Keep:
    - File remains unchanged

Delete:
    - File is permanently deleted using `os.remove()`

Quit:
    - Stops processing immediately

Notes
-----
- Files are permanently deleted
- Deleted files cannot be recovered automatically
- Files missing a subject line will not trigger bulk deletion
- The script skips files already deleted during processing
- Terminal screen is cleared between files for easier review
- All `.txt` files in the folder are processed

Technical Details
-----------------
Single-key input is handled using:
    - `msvcrt` on Windows
    - `tty` and `termios` on Unix-based systems

Screen clearing uses:
    - `cls` on Windows
    - `clear` on Unix-based systems

Intended Use
------------
This tool is intended to assist with:
    - Subject Access Request (SAR) review
    - Email triage workflows
    - eDiscovery review
    - Manual dataset cleanup
    - Rapid message filtering

This script provides technical tooling only and does not constitute legal advice.
"""


import os
import sys

TARGET_DIR = "./merged_outputs"


# --- clear screen ---
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# --- single keypress ---
def get_key():
    try:
        import msvcrt
        return msvcrt.getch().decode("utf-8").lower()
    except ImportError:
        import tty
        import termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def get_subject(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                if i == 4 and line.lower().startswith("subject:"):
                    return line.strip().lower().replace("subject:", "").strip()
    except:
        pass
    return None


def display_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        print("=" * 80)
        print(f"FILE: {os.path.basename(path)}")
        print("=" * 80 + "\n")
        print(content)

    except Exception as e:
        print(f"Error reading {path}: {e}")


def delete_matching_subject(files, subject):
    deleted = 0

    for file in files:
        path = os.path.join(TARGET_DIR, file)

        file_subject = get_subject(path)

        if file_subject == subject:
            try:
                os.remove(path)
                print(f"Deleted: {file}")
                deleted += 1
            except Exception as e:
                print(f"Error deleting {file}: {e}")

    return deleted


def main():
    files = sorted([f for f in os.listdir(TARGET_DIR) if f.lower().endswith(".txt")])

    i = 0
    while i < len(files):
        file = files[i]
        path = os.path.join(TARGET_DIR, file)

        if not os.path.exists(path):
            i += 1
            continue

        clear_screen()
        display_file(path)

        print("\n[k] keep   [d] delete   [q] quit")

        while True:
            key = get_key()

            if key == "k":
                print("\n-> kept")
                break

            elif key == "d":
                subject = get_subject(path)

                try:
                    os.remove(path)
                    print("\n-> deleted")
                except Exception as e:
                    print(f"\nError deleting {file}: {e}")
                    break

                if subject:
                    print(f"\nSubject: {subject}")
                    print("Delete all messages with this subject? (y/n)")

                    choice = get_key()
                    print(choice)

                    if choice == "y":
                        deleted = delete_matching_subject(files, subject)
                        print(f"Deleted {deleted} additional files")

                break

            elif key == "q":
                print("\nExiting.")
                return

        i += 1

    clear_screen()
    print("Done.")


if __name__ == "__main__":
    main()
