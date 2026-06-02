import subprocess
import json
import shutil


def run_semgrep(target_path: str) -> dict:
    if not shutil.which("semgrep"):
        return {"error": "Semgrep not installed", "results": []}
    try:
        result = subprocess.run(
            [
                "semgrep", "--config=auto", "--json", "--quiet",
                "--exclude=node_modules", "--exclude=venv",
                "--exclude=.venv", "--exclude=__pycache__",
                "--exclude=dist", "--exclude=build",
                "--exclude=.next", "--exclude=coverage",
                "--exclude=*.min.js",
                target_path
            ],
            capture_output=True, text=True, timeout=180
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
        return {"results": []}
    except subprocess.TimeoutExpired:
        return {"error": "Semgrep timed out", "results": []}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON from Semgrep", "results": []}
    except Exception as e:
        return {"error": str(e), "results": []}


def get_semgrep_version() -> str:
    try:
        r = subprocess.run(
            ["semgrep", "--version"],
            capture_output=True, text=True, timeout=10
        )
        return r.stdout.strip()
    except Exception:
        return "unknown"
