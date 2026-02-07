# Microsoft Purview — Subject Access Request Toolkit

This repository contains scripts and operational guidance to assist with performing Subject Access Requests (SARs) using Microsoft Purview eDiscovery tools.

It is written from a practical systems-administration perspective and focuses on reproducible extraction workflows rather than policy or legal interpretation.

---

## Overview

A typical SAR workflow using Microsoft Purview involves:

1. Obtaining appropriate permissions
2. Creating a case
3. Running a content search
4. Exporting results
5. Processing exported data (handled by scripts in this repo)

This document describes the first stages of that workflow.

---

## 1 — Access to Microsoft Purview

To perform SAR work you must be able to:

* Create eDiscovery cases
* Run searches
* Export results

If you are a **Global Administrator**, you can assign yourself the required permissions within Purview.

Typical capability required:

* Case creation
* Search execution
* Data export / extraction

(Exact role configuration may vary by tenant governance policy.)

---

## 2 — Create Case and Search

### Create Case

1. Open Microsoft Purview
2. Navigate to **eDiscovery**
3. Create a new case
4. Add yourself as a member (if required by workflow)

---

### Configure Search

#### Data Sources

Select:

* All people and groups
* Exchange
* SharePoint

---

#### Condition Builder

Use **Keyword Query Language (KQL)** with:

```
(subject:"firstname surname")
OR (attachmentnames:firstname surname*)
OR (filename: firstname surname*)
```

This targets:

* Email subject matches
* Attachment name matches
* SharePoint / OneDrive file name matches

Adjust naming patterns as needed.

---

## 3 — Export Settings

Use default export settings **except** disable:

* Organize data from different locations into separate folders or PSTs
* Include folder and path of the source

This produces a simplified structure for downstream processing.

---

## 4 — Export Output Structure

The export generates two ZIP files:

### items.1.001.all

Contains:

* Files from OneDrive
* Files from SharePoint

---

### psts.001.all

Contains:

* PST file with Exchange data

---

## Next Steps

Subsequent stages (covered elsewhere in this repository):

* PST processing
* Archive extraction
* File indexing
* Deduplication
* Reporting

---

## Disclaimer

This repository documents a technical workflow only.
It does not constitute legal guidance regarding SAR obligations or compliance interpretation.
