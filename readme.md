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
    1.filterv5.py
    2.redact_metadatav2.py
    3.redact_wordsv3.py
    redact_words.txt         # Custom redaction list
    school_staff.txt         # Staff names for redaction
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
python 1.filterv5.py
```

Dependency:

```
pip install beautifulsoup4
```

### Actions Performed

* Removes unnecessary metadata files:
    * conversationindex.txt
    * recipients.txt
* Filters attachments:
    * Keeps files containing the target name
    * Moves them to output.export/attachments
    * Deletes all others
* Converts HTML → clean .txt using BeautifulSoup
* Merges extracted content into:
    * combined_messages.txt (includes Subject/Date)
    * combined_appointments.txt
    * combined_meetings.txt
* Removes redundant PST folder structures (e.g. Items)

This produces a clean, structured dataset ready for redaction.

---

### 4 — Metadata & Email Redaction

Run:

```
python 2.redact_metadatav2.py
```

### Actions Performed

* Redacts header fields:
    * From, To, Cc, Sender, Return-Path, etc.
* Handles multi-line (folded) headers correctly
* Redacts all email addresses across content
* Preserves formatting and structure
* Safe to rerun

---

### 5 — Word & Name Redaction

Edit:

```
redact_words.txt
school_staff.txt
```

Then run:

```
python 3.redact_wordsv3.py
```

### Actions Performed

* Redacts specified words and phrases
* Supports multi-word names (e.g. full names)
* Case-insensitive whole-word matching
* Logs all matched/redacted terms
* Designed for iterative refinement

---

## Workflow Summary

```
Purview Export
      ↓
Extract PST
      ↓
1.filterv5.py
      ↓
2.redact_metadatav2.py
      ↓
3.redact_wordsv3.py
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
