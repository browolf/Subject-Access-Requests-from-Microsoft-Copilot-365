"""
filterv3.py — Purview SAR export filter + HTML-to-text normalizer

Purpose
- Prepares Microsoft Purview SAR export content for review and redaction.
- Cleans common export artefacts, reduces attachment noise, and converts HTML
  message bodies into plain text.

Where it fits in the workflow
1) Export ZIPs from Purview and extract locally
2) Extract PST (pffexport) into the working folder
3) Place/confirm working directory: output.export/
4) Run this script (filterv3.py)
5) Run redact_headers.py
6) Run redact_words.py

What this script does
- Deletes known metadata files:
  - conversationindex.txt
  - recipients.txt
- Filters attachments by filename:
  - Keeps and moves files whose filename contains the subject’s name
  - Deletes other files with document-like extensions (noise reduction)
- Moves kept attachments into:
  - output.export/attachments/
  - Uses collision-safe renaming: " (1)", " (2)", ...
- Removes certain empty folders (best-effort):
  - output.export/Search Root
  - output.export/SPAM Search Folder 2
  - output.export/Top of Personal Folders/Deleted Items
- Converts HTML message bodies to text:
  - Finds .html/.htm under output.export
  - Extracts visible text with BeautifulSoup (scripts/styles removed)
  - Writes .txt alongside the original file and deletes the HTML
  - Includes a small merge step so lines like "To:" / "From:" that appear on a
    separate line are joined with the following value line where appropriate

Inputs / Assumptions
- Working directory "output.export" exists (relative to where you run the script)
- You will be prompted for a match string:
  - "firstname surname" (case-insensitive)
- Attachment “keep” logic is filename-based only (not content-based)

Outputs
- Modified folder tree under output.export/
- Kept attachments moved into output.export/attachments/
- HTML files replaced with .txt equivalents

Dependencies
- Python 3.x
- beautifulsoup4
  Install:
    pip install beautifulsoup4

Usage
- Run from the folder that contains "output.export":
    python filterv3.py
- When prompted, enter:
    firstname surname

Operational Notes
- This script is destructive:
  - It deletes certain files and HTML sources after conversion.
  - Test on copies of exports if you need to preserve originals.
- Designed to be rerunnable in the same working folder, but:
  - Previously deleted items will not be recoverable.
  - HTML conversion is one-way (HTML removed after .txt is created).

Repository
- See /docs/purview-export.md for export settings and expected ZIP outputs.
- See /docs/pst-extraction.md for PST extraction using pff-tools.
"""


import os
import sys
import shutil
from bs4 import BeautifulSoup   # <-- imported here at the top


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
    from bs4 import BeautifulSoup

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

                # ----- FIX: Merge "To:", "From:", "Cc:", etc. with the next line -----
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
                # ---------------------------------------------------------------------

                cleaned_text = "\n".join(merged)

                # Write .txt
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_text)

                print(f"Converted HTML → {txt_path}")
                os.remove(html_path)
                print(f"Deleted: {html_path}")

            except Exception as e:
                print(f"Error converting '{html_path}': {e}")


def main():
    name = input("Enter the name to keep (firstname surname): ").strip().lower()

    target_dir = "output.export"
    attachments_dir = os.path.join(target_dir, "attachments")

    extensions = {".xlsx", ".docx", ".pdf", ".csv", ".doc", ".xls", "pptx", "ppt"}

    always_delete_filenames = {
        "conversationindex.txt", "recipients.txt"
    }

    if not os.path.isdir(target_dir):
        print(f"Folder '{target_dir}' not found.")
        sys.exit(1)

    for root, _, files in os.walk(target_dir):

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
                except:
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
                    except:
                        pass

    # Remove empty folders
    try_remove_if_empty(os.path.join(target_dir, "Search Root"))
    try_remove_if_empty(os.path.join(target_dir, "SPAM Search Folder 2"))
    try_remove_if_empty(os.path.join(target_dir, "Top of Personal Folders", "Deleted Items"))

    # Convert HTML → txt
    convert_html_to_text_simple(target_dir)


if __name__ == "__main__":
    main()
