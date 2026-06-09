import subprocess
import json
import shutil
import sys
import os


def _find_tool(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        for candidate in [
            os.path.join(exe_dir, name),
            os.path.join(exe_dir, name + ".exe"),
            os.path.join(exe_dir, "Scripts", name),
            os.path.join(exe_dir, "Scripts", name + ".exe"),
        ]:
            if os.path.isfile(candidate):
                return candidate
    scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
    for ext in ("", ".exe", ".cmd"):
        path = os.path.join(scripts_dir, name + ext)
        if os.path.isfile(path):
            return path
    return None


def _subprocess_flags():
    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kwargs


def run_semgrep(target_path: str) -> dict:
    semgrep = _find_tool("semgrep")
    if not semgrep:
        return {
            "error": "Semgrep not found. Run: pip install semgrep",
            "results": []
        }
    try:
        result = subprocess.run(
            [
                semgrep,
                "--config=auto",
                "--json",
                "--quiet",
                "--exclude=node_modules",
                "--exclude=venv",
                "--exclude=.venv",
                "--exclude=__pycache__",
                "--exclude=dist",
                "--exclude=build",
                "--exclude=.next",
                "--exclude=coverage",
                "--exclude=*.min.js",
                target_path
            ],
            capture_output=True, text=True, timeout=180,
            **_subprocess_flags()
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
        return {"results": []}
    except subprocess.TimeoutExpired:
        return {"error": "Semgrep timed out", "results": []}
    except json.JSONDecodeError:
        return {"error": "Semgrep returned invalid JSON", "results": []}
    except Exception as e:
        return {"error": str(e), "results": []}


def get_semgrep_version() -> str:
    semgrep = _find_tool("semgrep")
    if not semgrep:
        return "not installed"
    try:
        r = subprocess.run(
            [semgrep, "--version"],
            capture_output=True, text=True, timeout=10,
            **_subprocess_flags()
        )
        return r.stdout.strip()
    except Exception:
        return "unknown"