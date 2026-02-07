# Microsoft Purview — Subject Access Request Toolkit

This repository contains scripts and operational guidance to assist with processing Subject Access Requests (SARs) using Microsoft Purview eDiscovery exports.

It focuses on reproducible technical workflows for extracting and processing data — particularly Exchange, OneDrive, and SharePoint exports — rather than legal interpretation or compliance policy.

---

## Repository Structure

```
README.md
/docs
    purview-export.md      # Purview case/search/export workflow
    pst-extraction.md      # Extract PST contents to text
/scripts
    (processing and analysis scripts)
```

Documentation is split into stages so each part of the SAR workflow can be updated independently.

---

## Workflow Overview

Typical technical workflow covered by this repository:

1. Obtain permissions in Microsoft Purview
2. Create case and run search
3. Export results
4. Extract PST email content
5. Process and analyze extracted data (scripts)

---

## Stage 1 — Microsoft Purview Access

To perform SAR work you must be able to:

* Create eDiscovery cases
* Run searches
* Export results

If you are a **Global Administrator**, you can assign yourself the required permissions within Purview to perform these actions (subject to tenant governance policy).

---

## Stage 2 — Create Case and Search

### Data Sources

Select:

* All people and groups
* Exchange
* SharePoint

---

### Condition Builder (KQL)

Use Keyword Query Language:

```
(subject:"firstname surname")
OR (attachmentnames:firstname surname*)
OR (filename: firstname surname*)
```

This captures:

* Email subject matches
* Attachment name matches
* OneDrive / SharePoint filename matches

Adjust patterns as required.

---

## Stage 3 — Export Settings

Use default export configuration **except disable**:

* Organize data from different locations into separate folders or PSTs
* Include folder and path of the source

---

## Export Output

Purview export produces two archives:

### `items.1.001.all`

Contains:

* OneDrive files
* SharePoint files

---

### `psts.001.all`

Contains:

* PST archive of Exchange data

---

## Stage 4 — PST Extraction

Email content must be extracted from the PST archive before analysis.

This repository uses:

* Windows Subsystem for Linux (WSL)
* Ubuntu
* `libpff` (`pffexport`)

### Install WSL

Open PowerShell as Administrator:

```powershell
wsl --install -d Ubuntu
```

Reboot if prompted.

Launch Ubuntu and create a username/password.

---

### Install Extraction Tools

```bash
sudo apt update
sudo apt install -y pff-tools
```

Verify:

```bash
pffexport -h
```

---

### Access Windows Files

WSL mounts drives under `/mnt`

Examples:

```
C:\ → /mnt/c
E:\ → /mnt/e
```

Example paths:

```
PST file:
/mnt/e/purview/export.pst

Output directory:
/mnt/e/purview/output
```

Create output directory:

```bash
mkdir -p /mnt/e/purview/output
```

---

### Extract Email Content

```bash
pffexport -t /mnt/e/purview/output -f all /mnt/e/purview/export.pst
```

This will:

* Process all folders (including hidden/recoverable)
* Extract all messages
* Save emails as plain text files
* Export attachments

Large PST files may require significant processing time.

---

### Result

Output directory will contain a folder structure representing the mailbox.

Each message directory includes:

* Headers
* Body text
* Attachments

---

## Stage 5 — Further Processing

Scripts in `/scripts` may be used to:

* Index extracted data
* Search content
* Deduplicate results
* Generate reports

(Implementation varies by use case.)

---

## Disclaimer

This repository documents technical workflow only.
It does not constitute legal guidance regarding SAR obligations or compliance interpretation.
