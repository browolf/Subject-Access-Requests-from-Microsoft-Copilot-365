# Microsoft Purview — Case Creation & Export

This document describes the process for running a search and exporting data for a Subject Access Request (SAR) using Microsoft Purview.

---

## Permissions

You must be able to:

* Create eDiscovery cases
* Run searches
* Export results

A Global Administrator can assign themselves the required permissions if tenant governance allows.

---

## Create a Case

1. Open Microsoft Purview
2. Navigate to **eDiscovery**
3. Create a new case
4. Add yourself as a member if required

---

## Create a Search

### Data Sources

Select:

* All people and groups
* Exchange
* SharePoint

---

### Condition Builder (KQL)

Use:

```
(subject:"firstname surname")
OR (attachmentnames:firstname surname*)
OR (filename: firstname surname*)
```

This captures:

* Email subjects
* Attachment names
* OneDrive/SharePoint filenames

Adjust naming patterns as needed.

---

## Export Results

Use default export settings **except disable**:

* Organize data from different locations into separate folders or PSTs
* Include folder and path of the source

---

## Expected Output

### items.* archive

Contains:

* OneDrive files
* SharePoint files

---

### psts.* archive

Contains:

* PST file with Exchange mailbox data

---

## Next Step

Continue processing using repository workflow:

1. Download ZIP files
2. Extract PST using `/docs/pst-extraction.md`
3. Run filtering and redaction scripts
