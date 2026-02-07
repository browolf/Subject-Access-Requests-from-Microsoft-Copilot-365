# Microsoft Purview — Subject Access Request Toolkit

This repository provides scripts and operational guidance for processing Subject Access Requests (SARs) using Microsoft Purview exports.

It focuses on the technical workflow required to extract, filter, redact, and prepare data originating from:

* Exchange mailboxes
* OneDrive
* SharePoint

This documentation describes operational procedures only and does **not** constitute legal or compliance guidance.

---

## Repository Structure

```
README.md
/docs
    purview-export.md      # Purview case/search/export instructions
    pst-extraction.md      # Extract PST using pffexport
/scripts
    filterv3.py
    redact_headers.py
    redact_words.py
redact_words.txt           # Word list for iterative redaction
```

---

## End-to-End Workflow

### 1 — Export From Microsoft Purview

Run search and export data using Microsoft Purview.

Detailed instructions:

```
/docs/purview-export.md
```

Expected outputs:

| Archive   | Contents                    |
| --------- | --------------------------- |
| `items.*` | OneDrive / SharePoint files |
| `psts.*`  | Exchange PST                |

---

### 2 — Extract PST Content

Extract mailbox content using `pffexport`.

Full setup and usage:

```
/docs/pst-extraction.md
```

Result:

* Emails exported as text
* Attachments extracted
* Folder structure created under:

```
output.export/
```

---

### 3 — Filter & Normalize Export

Run:

```
python filterv3.py
```

Dependency:

```
pip install beautifulsoup4
```

### Actions Performed

* Removes empty folders
* Deletes metadata files

  * `conversationindex.txt`
  * `recipients.txt`
* Filters attachments

  * Keeps files containing subject name
  * Moves to `output.export/attachments`
  * Deletes others
* Converts HTML message bodies → `.txt`

This prepares content for redaction.

---

### 4 — Header & Address Redaction

Run:

```
python redact_headers.py
```

### Actions Performed

* Redacts identifying header fields
* Redacts remaining email addresses
* Preserves formatting
* Safe to rerun

---

### 5 — Keyword Redaction

Edit:

```
redact_words.txt
```

Then run:

```
python redact_words.py
```

### Actions Performed

* Redacts specified words/phrases
* Case-insensitive matching
* Reports redacted terms per file
* Designed for iterative use

---

## Workflow Summary

```
Purview Export
      ↓
Extract PST
      ↓
filterv3.py
      ↓
redact_headers.py
      ↓
redact_words.py
```

---

## Dependencies Summary

| Tool           | Purpose                    |
| -------------- | -------------------------- |
| WSL + Ubuntu   | PST extraction environment |
| pff-tools      | Extract Exchange PST       |
| Python 3       | Script execution           |
| beautifulsoup4 | HTML text extraction       |

---

## Operational Notes

* Scripts modify files in place
* Work on extracted copies of exports
* Redaction stages can be rerun safely
* Repository focuses on tooling — workflow governance is environment-specific

---

## Disclaimer

This repository documents technical workflow only.
It does not constitute legal advice or compliance guidance.
