# PST SAR Processing Toolkit

A collection of Python scripts designed to assist with processing Outlook PST exports for:

- Subject Access Requests (SARs)
- eDiscovery
- Internal investigations
- Email review workflows
- Dataset sanitisation and redaction

The toolkit extracts PST content, filters messages, removes unnecessary metadata, redacts sensitive information, and merges outputs into reviewable datasets.

---

# Workflow Overview

Recommended processing order:

```text
1.extract-pst.py
2.purge_parent_emails.py
3.remove_footer.py
4.review.py
5.redact.py
6.redact-part2.py
7.merge.py
xfinal-redact-merged(optional).py
xfix-redaction(optional).py
```

---

# File Overview

---

## 1.extract-pst.py

Main PST extraction and filtering script.

### Features

- Processes `.export` PST extraction folders
- Extracts:
  - Messages
  - Appointments
  - Meetings
- Converts HTML bodies into readable text
- Copies matching attachments
- Filters content using a supplied name
- Preserves useful metadata:
  - Subject
  - Date
  - Sender
  - Recipients

### Output

Creates:

```text
./merged_outputs/
```

Containing:

```text
00001_message.txt
00001_appointment.txt
00001_meeting.txt
attachments/
```

---

## 2.purge_parent_emails.py

Deletes messages where specified names appear within email headers.

### Searches

- `From:`
- `To:`

### Purpose

Useful for removing parent correspondence or excluding communications involving specific individuals.

---

## 3.footers.json

Configuration file containing regex patterns for removing repetitive email footer blocks.

### Example Use Cases

- Confidentiality notices
- Email signatures
- External email warnings
- Legal disclaimers

### Example Structure

```json
{
    "remove_blocks": [
        "EXTERNAL EMAIL.*?inspection\\."
    ]
}
```

---

## 3.remove_footer.py

Removes footer blocks defined in `3.footers.json`.

### Features

- Regex-based removal
- Multiline matching
- Preserves message headers
- Replaces removed sections with:

```text
[email footer removed]
```

---

## 4.review.py

Interactive terminal review tool.

### Controls

```text
[k] keep
[d] delete
[q] quit
```

### Features

- Displays one file at a time
- No Enter key required
- Optional bulk deletion by matching subject
- Full-screen review workflow

### Purpose

Manual triage and cleanup before disclosure or redaction.

---

## 5.redact.py

Primary automated redaction tool.

### Redacts

- Email addresses
- Staff names

### Features

- Uses exemptions list
- Boundary-aware matching
- Preserves headers
- Processes only message bodies

### Configuration Files

#### exemptions.json

```json
{
    "emails": [
        "allowed@example.com"
    ]
}
```

#### school_staff.txt

```text
John Smith
Jane Doe
```

---

## 6.redact-part2.py

Interactive manual redaction tool.

### Features

- Reviewer enters words manually
- Replaces matches with:

```text
<redacted>
```

- Saves entered words to:

```text
school_staff.txt
```

### Purpose

Useful for:
- Catching missed names
- Redacting uncommon identifiers
- Manual cleanup after automated redaction

---

## 7.merge.py

Merges processed files into consolidated datasets.

### Outputs

```text
merged_messages.txt
merged_appointments.txt
merged_meetings.txt
```

### Header Cleanup

Removes:
- `Source:`
- `From:`
- `To:`

Preserves:
- `Subject:`
- `Date:`

---

## school_staff.txt

List of staff names used for automated redaction.

### Format

One entry per line:

```text
John Smith
Jane Doe
```

Used by:
- `5.redact.py`
- `6.redact-part2.py`

---

## xfinal-redact-merged(optional).py

Optional final redaction stage for merged datasets.

### Features

- Processes:
  - `merged_messages_redacted.txt`
- Interactive workflow
- Skips:
  - Subject lines
  - Date lines
  - Divider lines

### Purpose

Final pass before disclosure or export.

---

## xfix-redaction(optional).py

Interactive unredaction / correction tool.

### Purpose

Corrects over-redaction mistakes.

### Example

Fixes:

```text
<redacted>int meeting
```

Back to:

```text
joint meeting
```

### Features

- Custom replacement values
- Interactive workflow
- Preserves headers
- Processes message bodies only

---

# Typical Workflow

## 1. Extract PST Content

Run:

```bash
python 1.extract-pst.py
```

---

## 2. Remove Unwanted Parent Emails

Run:

```bash
python 2.purge_parent_emails.py
```

---

## 3. Remove Email Footers

Run:

```bash
python 3.remove_footer.py
```

---

## 4. Manually Review Messages

Run:

```bash
python 4.review.py
```

---

## 5. Run Automated Redaction

Run:

```bash
python 5.redact.py
```

---

## 6. Perform Manual Redaction Cleanup

Run:

```bash
python 6.redact-part2.py
```

---

## 7. Merge Files

Run:

```bash
python 7.merge.py
```

---

## Optional Final Passes

### Final merged redaction:

```bash
python xfinal-redact-merged(optional).py
```

### Fix over-redaction mistakes:

```bash
python xfix-redaction(optional).py
```

---

# Requirements

Install dependencies:

```bash
pip install beautifulsoup4
```

---

# Notes

- Most scripts modify files in place
- Always work from copies of original exports
- Redaction is case-insensitive
- Headers are generally preserved during redaction stages
- Interactive tools permanently delete or overwrite files

---

# Intended Use

This toolkit is intended to assist with:

- Subject Access Request (SAR) preparation
- eDiscovery workflows
- Internal investigations
- Email dataset sanitisation
- Manual review and redaction workflows

This repository provides technical tooling only and does not constitute legal advice.

