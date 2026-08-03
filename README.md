<p align="center">
  <img src="assets/Logo.png" width="90" alt="SentinelAI logo"/>
</p>

<h1 align="center">SentinelAI App</h1>
<p align="center"><b>Intelligent SAST Validation and Severity Classification</b></p>
<p align="center">An AI-assisted desktop tool that reduces false positives and improves severity accuracy in Static Application Security Testing (SAST) workflows.</p>



## Overview

Static Application Security Testing (SAST) tools are notorious for flooding developers with **false positives**, which causes alert fatigue and wastes remediation time. SentinelAI sits on top of [Semgrep](https://semgrep.dev) and uses a large language model (OpenAI GPT-4 family) to:

- Automatically **triage** each raw finding as a true vulnerability or a false positive
- **Re-classify severity** for confirmed findings using CVSS-style reasoning
- Present a clean, auditable **before vs after** comparison so a security reviewer can see exactly how many findings were filtered and why
- Export the validated results as **PDF** and **JSON** reports

It is built as a Windows desktop application using PySide6 (Qt for Python), with a local SQLite database for scan history and AI verdict caching.

## How It Works

```
 Source Code
     │
     ▼
 ① Semgrep Scan  ───────────►  Raw findings (rule ID, CWE, file, line, snippet)
     │
     ▼
 ② Normalisation  ──────────►  Findings mapped to CWE IDs + severity levels
     │
     ▼
 ③ AI Validation (GPT)  ────►  Each finding classified TRUE_POSITIVE / FALSE_POSITIVE
     │
     ▼
 ④ AI Severity Re-check  ───►  Confirmed findings re-scored CRITICAL / HIGH / MEDIUM / LOW
     │
     ▼
 ⑤ Dashboard + Reports  ────►  Validated Findings by Severity, PDF/JSON export
```

## Features

- **Multi-language static scanning** via Semgrep (30+ languages, 1,000+ community rules)
- **AI false-positive detection** — every finding is sent to GPT with the surrounding code snippet and asked for a TRUE_POSITIVE / FALSE_POSITIVE verdict, confidence level, and a written justification
- **AI severity re-classification** — confirmed vulnerabilities are independently re-scored for severity, rather than trusting the scanner's default rating
- **CWE mapping** — raw scanner rule IDs (including Bandit-style check IDs) are normalised to official CWE identifiers and titles
- **Interactive dashboard** — total scans, raw findings, false positives filtered, true positives, and a severity breakdown donut chart
- **Scan history** — every scan is stored in a local database and can be revisited from the dashboard or Settings
- **Validation caching** — once a finding has been judged by the AI, the verdict is cached so re-viewing results doesn't re-call the API
- **PDF & JSON report export** — generate shareable reports per scan, saved to a folder of your choice
- **In-app API key management** — set/update your OpenAI API key from the Settings screen, no manual file editing required
- **Data management tools** — clear validations, delete individual project scan history, or wipe all app data from Settings
- **Dark sidebar / light workspace UI** with a custom Qt stylesheet (`styles/theme.qss`)

## Requirements

| Requirement | Version |
|---|---|
| OS | Windows 10/11 (primary target) |
| Python | 3.10 – 3.12 |
| Semgrep | 1.50.0+ |
| OpenAI API key | GPT-4 family access |

Python package dependencies (see `requirements.txt`):

```
PySide6>=6.6.0
openai>=1.10.0
semgrep>=1.50.0
reportlab>=4.0.0
matplotlib>=3.8.0
python-dotenv>=1.0.0
```

## Installation

There are two ways to run SentinelAI: from source (for development) or via the bundled Windows installer (for end users).

### Option A — Run from Source

```bash
# 1. Clone / extract the project
cd sentinelai

# 2. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your OpenAI API key
copy .env.example .env           # Windows
# cp .env.example .env           # macOS/Linux
# then open .env and set OPENAI_API_KEY=sk-...

# 5. Run the app
python main.py
```

### Option B — Windows Installer

A prebuilt installer (`SentinelAI_Setup.exe`) is produced with PyInstaller + Inno Setup:

1. Run `SentinelAI_Setup.exe` and complete the setup wizard.
   - The installer checks for a Python 3.9–3.12 install and silently installs Python 3.10 if none is found.
   - It then silently installs `semgrep` via pip so scanning works out of the box.
2. Launch **SentinelAI** from the Start Menu or Desktop shortcut.
3. On first launch, go to **Settings** and paste your OpenAI API key (see [Configuration](#configuration) below) — the installer does **not** ship a personal API key for security reasons.

> The installed app requires admin privileges (`PrivilegesRequired=admin`) because it installs Python/Semgrep system-wide.

## Configuration

SentinelAI reads its OpenAI API key from a `.env` file. **Where that file lives depends on how the app is running:**

| Run mode | `.env` / database location |
|---|---|
| Running from source (`python main.py`) | Project root folder (`sentinelai/.env`, `sentinelai/database/sentinel.db`) |
| Installed / bundled `.exe` | `%LOCALAPPDATA%\SentinelAI\.env` and `%LOCALAPPDATA%\SentinelAI\sentinel.db` |

You normally never need to touch this file directly — use the **Settings** screen inside the app, which writes the key to the correct location automatically:

1. Open the app → **Settings**
2. Paste your OpenAI API key into the API Key field
3. Click **Save**

If no key is configured, AI validation calls will fail and every finding will default to "True Positive" with a note in its reason field — always confirm a key is set before validating.

## Usage Guide

1. **Scan Code**
   Select a project folder to scan. SentinelAI runs Semgrep against it and parses the raw JSON output into normalised findings (CWE ID, severity, file, line, code snippet).

2. **Validate**
   Run AI validation on the raw findings. Each finding is sent individually (or in batches) to GPT, which returns:
   - a `TRUE_POSITIVE` / `FALSE_POSITIVE` verdict with a confidence level and reasoning
   - for confirmed findings, an independently re-assessed severity level with reasoning

3. **Results**
   Browse the validated findings list. Filter by severity, see which findings were removed as false positives and why, and inspect the AI's written justification for each verdict.

4. **Dashboard**
   Get an overview across all scans: total scans, raw findings, false positives filtered, true positives, and a donut chart of validated findings by severity. Click any row in **Recent Scans** to jump straight to its results.

5. **Export Report**
   Pick a scan and generate a PDF or JSON report summarising the validated findings, ready to share or archive.

6. **Settings**
   Manage your OpenAI API key, view aggregate stats, delete a project's scan history, clear cached validations, or wipe all app data.

## Folder Structure

```
sentinelai/
├── main.py                     # Application entry point
├── config.py                   # Loads .env / API key (location depends on frozen vs source)
├── requirements.txt            # Python dependencies
├── SentinelAI.spec             # PyInstaller build spec
├── SentinelAI_Setup.iss        # Inno Setup installer script
├── README.md
│
├── assets/
│   ├── Logo.png                 # App logo (UI)
│   └── Logo.ico                 # App/installer icon
│
├── styles/
│   └── theme.qss                 # Qt stylesheet (dark sidebar, light workspace)
│
├── scanner/
│   ├── semgrep_runner.py        # Locates & invokes the Semgrep binary, parses raw output
│   └── scan_manager.py          # Orchestrates a scan run and reports progress
│
├── parser/
│   ├── normaliser.py            # Converts raw Semgrep JSON into Finding objects
│   └── cwe_mapper.py            # Maps rule IDs / Bandit check IDs to CWE identifiers & titles
│
├── llm/
│   ├── prompt_builder.py        # Builds the FP-detection and severity-classification prompts
│   └── ai_classifier.py         # Calls the OpenAI API, parses verdicts, handles caching/errors
│
├── database/
│   ├── db_manager.py            # SQLite connection, CRUD for scans/findings/validations
│   ├── schema.sql               # Table definitions (scans, findings, validations)
│   └── sentinel.db              # Local SQLite database (created at runtime)
│
├── reports/
│   ├── pdf_generator.py         # Builds PDF reports with ReportLab
│   └── json_exporter.py         # Builds JSON report exports
│
├── ui/
│   ├── main_window.py           # Main window shell, sidebar navigation, screen routing
│   ├── splash_screen.py         # Startup splash / landing screen
│   ├── dashboard.py             # Dashboard screen (stat cards, donut chart, recent scans)
│   ├── upload_panel.py          # "Scan Code" screen — folder picker + scan trigger
│   ├── validate_panel.py        # "Validate" screen — runs AI validation, shows progress
│   ├── results_panel.py         # "Results" screen — findings list with AI verdicts
│   ├── report_panel.py          # "Export Report" screen — PDF/JSON export controls
│   └── settings_panel.py        # "Settings" screen — API key, stats, data management
│
├── datasets/
│   └── custom/                   # Custom evaluation datasets (for testing/thesis evaluation)
│
├── evaluation/                   # Evaluation scripts / metrics (accuracy, precision, recall etc.)
│
└── exports/                      # Default output folder for generated PDF/JSON reports
```

## Architecture

SentinelAI follows a simple layered pipeline, wired together by the Qt UI:

| Layer | Responsibility | Key files |
|---|---|---|
| **Scanning** | Run Semgrep against the target project and capture raw JSON output | `scanner/semgrep_runner.py`, `scanner/scan_manager.py` |
| **Parsing / Normalisation** | Convert raw scanner output into a consistent `Finding` dataclass with CWE + severity | `parser/normaliser.py`, `parser/cwe_mapper.py` |
| **AI Validation** | Prompt-engineer and call GPT for false-positive detection and severity re-classification | `llm/prompt_builder.py`, `llm/ai_classifier.py` |
| **Persistence** | Store scans, findings, and AI validation verdicts; cache verdicts by `finding_id` | `database/db_manager.py`, `database/schema.sql` |
| **Reporting** | Generate PDF/JSON deliverables from validated findings | `reports/pdf_generator.py`, `reports/json_exporter.py` |
| **Presentation** | PySide6 desktop UI — dashboard, scan/validate/results/report/settings screens | `ui/*.py` |

The AI classifier (`llm/ai_classifier.py`) is the core "intelligence" layer: it builds a prompt per finding (via `prompt_builder.py`), calls the OpenAI Chat Completions API, parses the structured `VERDICT` / `CONFIDENCE` / `REASON` response, and writes the result back into the `validations` table. Results are cached by `finding_id`, so re-opening a previously validated scan does not re-call the API.

## Database Schema

SentinelAI uses a local SQLite database (`sentinel.db`) with three tables:

**`scans`** — one row per scan run
| Column | Description |
|---|---|
| `scan_id` | Primary key |
| `project_name`, `project_path` | What was scanned |
| `scan_timestamp` | When the scan ran |
| `total_findings`, `validated_findings`, `false_positives` | Summary counters |
| `critical_count` / `high_count` / `medium_count` / `low_count` | Severity breakdown |
| `semgrep_version` | Version of Semgrep used |

**`findings`** — one row per raw finding
| Column | Description |
|---|---|
| `finding_id` | Primary key (UUID) |
| `scan_id` | Foreign key → `scans` |
| `cwe_id`, `title`, `severity`, `confidence` | Classification metadata |
| `file_path`, `line_number`, `code_snippet` | Location and context |
| `scanner`, `rule_id` | Which tool/rule produced it |

**`validations`** — one row per AI verdict, keyed to a finding
| Column | Description |
|---|---|
| `validation_id` | Primary key |
| `finding_id` | Foreign key → `findings` |
| `is_false_positive` | AI's TRUE/FALSE verdict |
| `fp_reason` | AI's written justification |
| `ai_severity`, `ai_severity_reason` | AI's re-assessed severity + reasoning |
| `original_severity` | Severity before AI re-classification |
| `validated_at`, `model_used` | Audit trail |

## Building the Installer

To produce a distributable Windows installer from source:

```bash
# 1. Build the frozen executable
pip install pyinstaller
pyinstaller SentinelAI.spec

# This produces dist/SentinelAI/SentinelAI.exe plus dependencies

# 2. Build the installer (requires Inno Setup: https://jrsoftware.org/isinfo.php)
#    Place python-3.10.11-amd64.exe in the project root first (used for silent Python install)
iscc SentinelAI_Setup.iss

# Output: installer_output/SentinelAI_Setup.exe
```

Notes on the build:
- `semgrep` is intentionally **excluded** from the PyInstaller bundle (`excludes=['semgrep']` in the `.spec`) and installed separately via pip by the Inno Setup script post-install, since it ships its own binaries that don't freeze cleanly.
- The `.env` file (containing your personal API key) is **not** bundled into the installer for security — end users must configure their own key via Settings after installing.

## Known Limitations

- **AI verdicts are not perfectly deterministic.** Even with `temperature=0`, GPT-family models can occasionally give a different verdict for the same borderline finding across separate runs, due to inference-time batching on the provider's infrastructure. Clear-cut findings are stable; a small number of ambiguous findings may vary run to run. Cached verdicts (in `sentinel.db`) remain stable until explicitly cleared.
- **Source vs installed builds use separate data locations.** Running from source reads/writes `.env` and `sentinel.db` in the project folder; the installed app uses `%LOCALAPPDATA%\SentinelAI`. The two do not share a validation cache.
- **Requires an active OpenAI API key with available quota.** Without one, AI validation calls fail and findings default to "True Positive."
- **Windows-first.** The installer and Python/Semgrep auto-install logic target Windows specifically.

