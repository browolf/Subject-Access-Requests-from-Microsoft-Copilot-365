# PST Extraction Instructions (WSL + libpff)

These steps describe how to extract email content from Microsoft Purview PST exports using Windows Subsystem for Linux (WSL) and `pffexport`.

---

## Install WSL and Ubuntu

Open **PowerShell as Administrator**

Run:

```powershell
wsl --install -d Ubuntu
```

Reboot if prompted.

Open **Ubuntu** from the Start menu.

Create a Linux username and password when prompted.

You should now see a Linux shell prompt.

---

## Update Ubuntu

```bash
sudo apt update
```

---

## Install libpff tools

```bash
sudo apt install -y pff-tools
```

This installs the `pffexport` utility.

---

## Verify Installation

```bash
pffexport -h
```

If help text is displayed, the tool is installed correctly.

---

## Locate Files in WSL

Windows drives are mounted under `/mnt`.

Examples:

```
C:\  →  /mnt/c
E:\  →  /mnt/e
```

Example paths:

```
PST file:     /mnt/e/purview/export.pst
Output folder:/mnt/e/purview/output
```

Create the output folder if needed:

```bash
mkdir -p /mnt/e/purview/output
```

---

## Extract Emails

Run:

```bash
pffexport -t /mnt/e/purview/output -f all /mnt/e/purview/export.pst
```

This will:

* Process all folders (including hidden and recoverable items)
* Extract all emails
* Save each email as plain text files

Large PST files may take time to complete.

---

## Output

The output directory will contain folders and text files representing the PST structure.

Each message folder contains:

* Email headers
* Message body
* Attachments
