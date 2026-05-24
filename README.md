# CRYPTX — AI-Powered Password Vulnerability Analyzer

> **Ethical security testing toolkit · Authorized use only**  
> Developed during Cyber Security Internship @ Supraja Technologies

---

## Table of Contents

- [Project Overview](#project-overview)
- [Team](#team)
- [Requirements](#requirements)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Building the EXE](#building-the-exe)
- [Project Structure](#project-structure)
- [Modules](#modules)
- [Troubleshooting](#troubleshooting)

---

## Project Overview

CryptX is an advanced cybersecurity toolkit designed to analyze password vulnerabilities and help organizations evaluate the strength of authentication systems.

The system integrates multiple password cracking techniques such as dictionary attacks, brute force attacks, rule-based mutations, rainbow tables, and AI-assisted wordlist generation to simulate real-world attack scenarios.

| Field             | Details                                          |
|-------------------|--------------------------------------------------|
| Project Name      | CryptX: AI-Powered Password Vulnerability Analyzer |
| Category          | Cyber Security / Password Analysis Tool          |
| Technologies      | Python, Tkinter, Hash Algorithms, AI Wordlist    |
| Start Date        | 01 January 2026                                  |
| Completion Date   | 01 May 2026                                      |
| Status            | ✅ Completed                                     |

---

## Team

| Name                  | Employee ID  | Email                              |
|-----------------------|--------------|------------------------------------|
| C Parasuraman         | ST#IS#9059   | parasuramanm492@gmail.com          |
| S Sai Manikanta Rao   | ST#IS#9060   | sainenisaimanikantarao@gmail.com   |
| P Prashanth           | ST#IS#9061   | prashanthpendem2323@gmail.com      |
| Sai Nikhil            | ST#IS#9062   | sainikhilyadav8@gmail.com          |
| V Rishika             | ST#IS#9072   | rishikav0105@gmail.com             |

**Organization:** Supraja Technologies · Cyber Security Internship  
**Contact:** contact@suprajatechnologies.com

---

## Requirements

- Python **3.10 or higher** (3.13 recommended)
- pip / conda package manager
- Windows 10 / 11 (64-bit)

---

## Installation & Setup

### Step 1 — Clone or Download the Project

```bash
git clone https://github.com/your-repo/CryptX.git
cd CryptX/PasswordCracker
```

Or extract the ZIP and open a terminal inside the `PasswordCracker` folder.

---

### Step 2 — Create a Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

> If you are using **Anaconda**, you can skip this step and use the base environment.

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing, install manually:

```bash
pip install pillow pyinstaller requests
```

---

### Step 4 — Verify Resources Folder

Make sure the `resources/` folder contains these files:

```
resources/
├── icon.ico        ← app icon (required for EXE)
├── logo.png        ← shown in the GUI header
├── logo1.png
└── supraja.png     ← company logo in project info
```

---

## Running the Application

```bash
python main.py
```

The CryptX launcher window will open. Use the mode selector (Beginner / Advanced / Report) and click any module card to get started.

---

## Building the EXE

### Step 1 — Install PyInstaller

```bash
pip install pyinstaller
```

---

### Step 2 — Build the EXE

Run this command from inside the `PasswordCracker` folder:

```bash
pyinstaller --onefile --windowed --add-data "resources;resources" --icon=resources/icon.ico --name "CryptX" main.py
```

| Flag | Purpose |
|------|---------|
| `--onefile` | Bundles everything into a single `.exe` |
| `--windowed` | Hides the black console window |
| `--add-data "resources;resources"` | Includes images and assets |
| `--icon=resources/icon.ico` | Sets the taskbar/desktop icon |
| `--name "CryptX"` | Names the output file `CryptX.exe` |

---

### Step 3 — Find Your EXE

After the build completes, your executable is here:

```
PasswordCracker/
└── dist/
    └── CryptX.exe   ✅  ← Share this file
```

> The `build/` folder and `CryptX.spec` file are generated automatically and can be deleted after the build.

---

### Step 4 — Run the EXE

Double-click `dist/CryptX.exe` — no Python installation needed on the target machine.

---

## Project Structure

```
PasswordCracker/
│
├── main.py                  ← Entry point
├── requirements.txt
├── README.md
│
├── resources/               ← Images and assets
│   ├── icon.ico
│   ├── logo.png
│   ├── logo1.png
│   └── supraja.png
│
├── ui/                      ← All GUI windows
│   ├── launcher_window.py
│   ├── hash_cracker_window.py
│   ├── hybrid_attack_window.py
│   ├── wordlist_generator_window.py
│   ├── ai_training_window.py
│   ├── rainbow_table_window.py
│   ├── analytics_window.py
│   ├── reports_window.py
│   ├── rule_engine_window.py
│   ├── advanced_mode.py
│   ├── reports_mode.py
│   └── project_info_window.py
│
├── core/                    ← Backend logic
└── data/                    ← Wordlists, rainbow tables, logs
```

---

## Modules

| Window | Module | Description |
|--------|--------|-------------|
| 1 | GUI Launcher | Main interface with mode selector |
| 2 | Hash Detection | Detects MD5, SHA1, SHA256, SHA512, NTLM |
| 3 | Hybrid Attack Engine | Dictionary + rules + brute force |
| 4 | AI Wordlist Generator | Smart lists from target metadata |
| 5 | Rule Engine | Hashcat-style transformations |
| 6 | Rainbow Table Manager | Lookup tables and DB stats |
| 7 | Analytics Dashboard | Strength metrics and crack charts |
| 8 | Reporting System | Audit reports and compliance logs |

---

## Troubleshooting

**`FileNotFoundError: icon.ico not found`**  
→ Make sure you use `icon.ico` not `logo.ico` in the build command:
```bash
--icon=resources/icon.ico
```

**Images not showing after building EXE**  
→ Add this helper to `main.py` and wrap all resource paths with it:
```python
import sys, os

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
```

**`ModuleNotFoundError` when running EXE**  
→ Add the missing module to your build command:
```bash
--hidden-import module_name
```

**Antivirus flags the EXE**  
→ This is a common false positive with PyInstaller. Whitelist the file or submit it for analysis.

**EXE is slow to open**  
→ Normal for `--onefile`. For faster startup use `--onedir` instead (produces a folder instead of a single file).

---

## License

This project was developed for educational and internship purposes at **Supraja Technologies**.  
Unauthorized use, distribution, or modification is not permitted.

---

*© 2026 CryptX Security · Supraja Technologies*
