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

Meetings

```
(
kind:meetings
AND firstname
AND Surname
)

or AND "firstname surname"
```

Email

```
kind:email

AND firstname
AND surname
AND sent>=2025-09-03
AND (NOT from:synergy-email)
AND (NOT recipients:(distributionlist OR distributionlist OR prefix))
AND (NOT sar OR "subject access request")
AND (NOT Subject:"Reaction Daily Digest")
```

Files

```
firstname AND surname
AND created>=2025-09-03
```

For email and files adjust data sources to mailboxes or sharepoint according. 

---

## Export Results

For files untick  "Organize data from different locations into separate folders or PSTs" and "Include folder and path of the source"

For email only untick "Include folder and path of the source"

Set the max sizes to whatever your prefer. I like 2GB

---

## Expected Output

### items.* archive

Contains:

* OneDrive files
* SharePoint files

---

### psts.* archive

Contains:

* a PST file for every user 

---

## Next Step

Continue processing using repository workflow:

1. Download ZIP files
2. Extract PST using `/docs/pst-extraction.md`
3. Run filtering and redaction scripts
