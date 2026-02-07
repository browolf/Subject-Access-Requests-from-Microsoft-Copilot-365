# Microsoft Purview — Subject Access Request Toolkit

This repository contains scripts and operational guidance to assist with processing Subject Access Requests (SARs) using Microsoft Purview exports.

It documents a practical technical workflow used to extract, process, filter, and redact data originating from Exchange, OneDrive, and SharePoint.

This guidance focuses on reproducible operational steps rather than legal interpretation or compliance policy.

---

## Repository Structure

```
README.md
/docs
    purview-export.md
    pst-extraction.md
/scripts
    filterv3.py
    redact_headers.py
    redact_words.py
```

---

## End-to-End Process Flow

### 1 — Export from Purview

* Run search within Microsoft Purview
* Export results
* Download ZIP archives locally

Expected outputs:

* `items.*.zip` — OneDrive/SharePoint files
* `psts.*.zip` — Exchange mailbox PST

---

### 2 — Case Folder Setup

Create a working directory for the request:

```
Teams/cases/<pupil-name>/
```

Upload:

* Extracted ZIP contents
* PST archive

This folder becomes the working location for processing.

---

### 3 — PST Extraction

Extract email content using `pff-tools`.

```bash
pffexport -t <output-folder> -f all <pst-file>
```

This:

* Processes all folders (including recoverable items)
* Exports messages to text
* Extracts attachments

See `/docs/pst-extraction.md` for full setup instructions.

---

### 4 — Filtering Stage

Run:

```bash
python filterv3.py
```

Requires:

```
beautifulsoup4
```

#### Actions Performed

* Deletes empty folders

* Deletes metadata files:

  * `conversationindex.txt`
  * `recipients.txt`

* Moves attachments containing the pupil's name in the filename to:

```
output.export/attachments
```

* Deletes other attachments

* Extracts readable text from HTML message files

---

### 5 — Header Redaction

Run:

```bash
python redact_headers.py
```

#### Redacts

The following fields:

* sender name
* sender email address
* sent representing name
* sent representing email address
* from
* to
* cc
* return-path

Also redacts:

* Any remaining email addresses detected in content

---

### 6 — Word Redaction

Run:

```bash
python redact_words.py
```

This script:

* Redacts terms listed in:

```
redact_words.txt
```

The file can be edited and the script rerun as required during review.

This supports iterative redaction as additional sensitive terms are identified.

---

## Workflow Summary

```
Purview Export
      ↓
Download ZIP files
      ↓
Create Case Folder
      ↓
Upload & Extract Files
      ↓
Extract PST (pffexport)
      ↓
filterv3.py
      ↓
redact_headers.py
      ↓
redact_words.py
```

---

## Disclaimer

This repository documents technical workflow only.
It does not constitute legal guidance regarding SAR obligations or compliance interpretation.
