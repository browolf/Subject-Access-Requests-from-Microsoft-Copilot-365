"""
# PDF Redaction Tool

A desktop GUI application for batch redacting text from PDF files using
PyMuPDF (`fitz`) and CustomTkinter.

## Features

- Batch redaction across all PDFs in the current folder
- Automatic backup creation before modification
- Manual single-text redaction
- Regex-safe whole word matching
- Persistent redact list loading from `redacts.txt`
- Multi-threaded processing to keep the UI responsive
- Live PDF preview with zoom support
- Real-time logging panel
- Simple file navigation between PDFs

## Requirements

- Python 3.10+
- PyMuPDF
- customtkinter
- Pillow

## Install

pip install pymupdf customtkinter pillow

## Usage

1. Place the script in a folder containing PDF files
2. (Optional) Create `redacts.txt` with one redact term per line
3. Run the script
4. Use:
   - "Auto Redact" to apply saved redact terms
   - "Redact" for manual one-off redactions
   - "Next File" to browse PDFs
   - "Apply Zoom" to change preview scale

## Notes

- Original PDFs are automatically backed up into `/backups`
- Redactions permanently modify the PDF
- `redacts.txt` is read-only in this version
- Matching is case-insensitive
- Auto redact uses whole-word regex matching
- Manual redact uses partial text matching
"""

import os
import shutil
import fitz
import customtkinter as ctk
import threading
import traceback
import re
from PIL import Image

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BACKUP_DIR = "backups"
REDACTS_FILE = "redacts.txt"

zoom_factor = 1.25

# -----------------------------
# Backup
# -----------------------------
def ensure_backups(pdf_files):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for pdf in pdf_files:
        dst = os.path.join(BACKUP_DIR, pdf)
        if not os.path.exists(dst):
            shutil.copy2(pdf, dst)

# -----------------------------
# Redacts (LOAD ONLY ✅)
# -----------------------------
def load_redacts():
    if not os.path.exists(REDACTS_FILE):
        return set()
    with open(REDACTS_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

# ❌ save_redact REMOVED (no writing anymore)

# -----------------------------
# Logging
# -----------------------------
def safe_log(msg):
    def write():
        log_box.insert("end", msg)
        log_box.see("end")
    app.after(0, write)

# -----------------------------
# REDACTION
# -----------------------------
def batch_redact_all_words(words, use_regex):
    words = list({w.lower(): w for w in words}.values())

    safe_log("\nStarting redaction\n\n")

    for index, pdf_path in enumerate(pdf_files, start=1):
        try:
            doc = fitz.open(pdf_path)
            word_totals = {word: 0 for word in words}

            for page in doc:
                page_hit = False
                words_on_page = page.get_text("words")

                for word in words:
                    if use_regex:
                        pattern = re.compile(
                            rf"(?<!\\w){re.escape(word)}(?!\\w)",
                            re.IGNORECASE
                        )

                    for w in words_on_page:
                        text = w[4]

                        if use_regex:
                            clean_text = re.sub(r"^\\W+|\\W+$", "", text)
                            match = pattern.fullmatch(clean_text)
                        else:
                            match = word.lower() in text.lower()

                        if match:
                            rect = fitz.Rect(w[:4])
                            page.add_redact_annot(rect, fill=(0, 0, 0))
                            word_totals[word] += 1
                            page_hit = True

                if page_hit:
                    page.apply_redactions()

            temp = pdf_path + ".tmp"
            doc.save(temp)
            doc.close()
            os.replace(temp, pdf_path)

            any_output = False
            output_lines = []

            for word, count in word_totals.items():
                if count > 0:
                    output_lines.append(f"  {word} {count}\n")
                    any_output = True

            if use_regex:
                safe_log(f"Redacting [{index}/{len(pdf_files)}] {pdf_path}\n")

                if any_output:
                    for line in output_lines:
                        safe_log(line)
                else:
                    safe_log("  (no matches)\n")

                safe_log("\n")

            else:
                if any_output:
                    safe_log(f"[{index}/{len(pdf_files)}] {pdf_path}\n")
                    for line in output_lines:
                        safe_log(line)
                    safe_log("\n")

        except Exception:
            safe_log("  ERROR\n")
            safe_log(traceback.format_exc() + "\n\n")

    safe_log("✅ Done\n")
    safe_log("🔄 Reloading current PDF...\n")
    app.after(0, load_pdf)

# -----------------------------
# Thread runner
# -----------------------------
def run_thread(words, use_regex):
    def worker():
        try:
            batch_redact_all_words(words, use_regex)
        except Exception:
            safe_log(traceback.format_exc())

    threading.Thread(target=worker, daemon=True).start()

# -----------------------------
# Rendering
# -----------------------------
def render_pdf():
    doc = fitz.open(pdf_files[current_index])
    images = []

    for page in doc:
        mat = fitz.Matrix(zoom_factor, zoom_factor)
        pix = page.get_pixmap(matrix=mat)

        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        ctk_img = ctk.CTkImage(
            light_image=pil_img,
            dark_image=pil_img,
            size=(pix.width, pix.height)
        )

        images.append(ctk_img)

    return images

def load_pdf():
    file_label.configure(
        text=f"[{current_index+1}/{len(pdf_files)}] {pdf_files[current_index]}"
    )

    for w in viewer_frame.winfo_children():
        w.destroy()

    images = render_pdf()

    for img in images:
        lbl = ctk.CTkLabel(viewer_frame, image=img, text="")
        lbl.image = img
        lbl.pack(pady=5)

# -----------------------------
# Zoom
# -----------------------------
def apply_zoom():
    global zoom_factor
    try:
        zoom_factor = float(zoom_entry.get())
        load_pdf()
    except:
        pass

# -----------------------------
# Navigation
# -----------------------------
def next_file():
    global current_index
    current_index = (current_index + 1) % len(pdf_files)
    load_pdf()

# -----------------------------
# Setup
# -----------------------------
pdf_files = [f for f in os.listdir(".") if f.lower().endswith(".pdf")]

if not pdf_files:
    print("No PDFs found.")
    exit()

ensure_backups(pdf_files)
current_index = 0

# -----------------------------
# UI
# -----------------------------
app = ctk.CTk()
app.title("PDF Redaction Tool")
app.geometry("1400x800")

viewer_container = ctk.CTkFrame(app)
viewer_container.pack(side="left", fill="both", expand=True)

control_panel = ctk.CTkFrame(app, width=250)
control_panel.pack(side="left", fill="y")

log_panel = ctk.CTkFrame(app)
log_panel.pack(side="right", fill="both", expand=True)

# ✅ file label
file_label = ctk.CTkLabel(viewer_container, text="", anchor="w")
file_label.pack(fill="x", padx=10, pady=5)

viewer_scroll = ctk.CTkScrollableFrame(viewer_container)
viewer_scroll.pack(fill="both", expand=True)
viewer_frame = viewer_scroll

# -----------------------------
# Controls (ORIGINAL ORDER ✅)
# -----------------------------
def auto_redact():
    words = load_redacts()
    if words:
        run_thread(list(words), use_regex=True)

btn_auto = ctk.CTkButton(control_panel, text="Auto Redact", command=auto_redact)
btn_auto.pack(pady=10, padx=10)

entry = ctk.CTkEntry(control_panel, placeholder_text="Enter text to redact")
entry.pack(pady=20, padx=10)

def on_redact_click():
    text = entry.get().strip()
    if not text:
        return

    # ✅ NO SAVE HERE ANYMORE
    run_thread([text], use_regex=False)

btn_redact = ctk.CTkButton(control_panel, text="Redact", command=on_redact_click)
btn_redact.pack(pady=10)

btn_next = ctk.CTkButton(control_panel, text="Next File", command=next_file)
btn_next.pack(pady=10)

# ✅ Zoom controls
zoom_entry = ctk.CTkEntry(control_panel, placeholder_text="Zoom (e.g. 1.25)")
zoom_entry.insert(0, "1.25")
zoom_entry.pack(pady=20, padx=10)

btn_zoom = ctk.CTkButton(control_panel, text="Apply Zoom", command=apply_zoom)
btn_zoom.pack(pady=5)

# -----------------------------
# Log
# -----------------------------
log_box = ctk.CTkTextbox(log_panel)
log_box.pack(fill="both", expand=True, padx=10, pady=10)

# -----------------------------
# Startup
# -----------------------------
load_pdf()
safe_log("Ready.\n")

saved_words = load_redacts()

if saved_words:
    safe_log("Loaded redacts.txt:\n")
    for w in saved_words:
        safe_log(f" - {w}\n")
else:
    btn_auto.configure(state="disabled")

app.mainloop()
