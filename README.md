# SentinelAI

**Intelligent SAST Validation and Severity Classification**

An AI-assisted pipeline that reduces false positives and improves severity classification in Static Application Security Testing workflows.

## What it does

1. Scans source code using Semgrep (30+ languages, 1,000+ rules)
2. Sends each finding to GPT-4 for false positive detection
3. Re-classifies severity for validated findings using AI
4. Presents before vs after comparison on a clean desktop dashboard
5. Exports PDF and JSON security reports

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OpenAI API key to .env
python main.py
```

## Requirements

- Python 3.10+
- Semgrep (`pip install semgrep`)
- OpenAI API key

## Project

- Student: Taiwo Victor Ayodele (A00059088)
- Supervisor: Badis Aoun
- University: University of Roehampton
- Programme: MSc Cybersecurity 2024–2025
