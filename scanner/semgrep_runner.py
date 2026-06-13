import subprocess
import json
import shutil
import sys
import os


def _find_tool(name: str) -> str:
    # 1. Check system PATH
    found = shutil.which(name)
    if found:
        return found

    # 2. Check exe directory (frozen build)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        for candidate in [
            os.path.join(exe_dir, name),
            os.path.join(exe_dir, name + ".exe"),
            os.path.join(exe_dir, name + ".EXE"),
            os.path.join(exe_dir, "Scripts", name),
            os.path.join(exe_dir, "Scripts", name + ".exe"),
            os.path.join(exe_dir, "Scripts", name + ".EXE"),
        ]:
            if os.path.isfile(candidate):
                return candidate

    # 3. Scripts folder next to sys.executable
    scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
    for ext in ("", ".exe", ".EXE", ".cmd"):
        path = os.path.join(scripts_dir, name + ext)
        if os.path.isfile(path):
            return path

    # 4. Common Program Files locations (all-users Python install)
    for ver in ["Python310", "Python311", "Python312", "Python39"]:
        for ext in ("", ".exe", ".EXE", ".cmd"):
            for base in [r"C:\Program Files", r"C:\Program Files (x86)", r"C:", r"D:"]:
                path = os.path.join(base, ver, "Scripts", name + ext)
                if os.path.isfile(path):
                    return path

    # 5. AppData per-user Python install
    appdata = os.environ.get("LOCALAPPDATA", "")
    if appdata:
        for ver in ["Python310", "Python311", "Python312", "Python39"]:
            for ext in ("", ".exe", ".EXE", ".cmd"):
                path = os.path.join(appdata, "Programs", "Python", ver, "Scripts", name + ext)
                if os.path.isfile(path):
                    return path

    # 6. Registry lookup
    try:
        import winreg
        for reg_root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for version in ["3.10", "3.11", "3.12", "3.9"]:
                try:
                    key = winreg.OpenKey(
                        reg_root,
                        f"SOFTWARE\\Python\\PythonCore\\{version}\\InstallPath"
                    )
                    install_path, _ = winreg.QueryValueEx(key, "")
                    winreg.CloseKey(key)
                    for ext in ("", ".exe", ".EXE", ".cmd"):
                        path = os.path.join(install_path, "Scripts", name + ext)
                        if os.path.isfile(path):
                            return path
                except Exception:
                    continue
    except Exception:
        pass

    return None


def _subprocess_flags():
    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kwargs


def _write_debug(content: str):
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.isdir(desktop):
            desktop = os.path.expanduser("~")
        path = os.path.join(desktop, "sentinel_semgrep_debug.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass


def run_semgrep(target_path: str) -> dict:
    debug_lines = []
    debug_lines.append(f"=== SENTINEL SEMGREP DEBUG ===")
    debug_lines.append(f"frozen = {getattr(sys, 'frozen', False)}")
    debug_lines.append(f"sys.executable = {sys.executable}")
    debug_lines.append(f"target_path = {target_path}")

    semgrep = _find_tool("semgrep")
    debug_lines.append(f"semgrep path found = {semgrep}")

    if not semgrep:
        debug_lines.append("RESULT: Semgrep not found")
        _write_debug("\n".join(debug_lines))
        return {
            "error": "Semgrep not found. Run: pip install semgrep",
            "results": []
        }

    cmd = [
        semgrep,
        "--config=auto",
        "--json",
        "--quiet",
        "--no-git-ignore",
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
    ]
    debug_lines.append(f"command = {cmd}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=180,
            stdin=subprocess.PIPE,
            **_subprocess_flags()
        )
        debug_lines.append(f"return code = {result.returncode}")
        debug_lines.append(f"stdout length = {len(result.stdout)}")
        debug_lines.append(f"stderr length = {len(result.stderr)}")
        debug_lines.append(f"stderr (first 2000 chars):")
        debug_lines.append(result.stderr[:2000])
        debug_lines.append(f"stdout (first 500 chars):")
        debug_lines.append(result.stdout[:500])

        if result.stdout.strip():
            data = json.loads(result.stdout)
            count = len(data.get("results", []))
            debug_lines.append(f"PARSED findings count = {count}")
            _write_debug("\n".join(debug_lines))
            return data

        debug_lines.append("RESULT: empty stdout")
        _write_debug("\n".join(debug_lines))
        return {"results": []}
    except subprocess.TimeoutExpired:
        debug_lines.append("RESULT: timeout")
        _write_debug("\n".join(debug_lines))
        return {"error": "Semgrep timed out", "results": []}
    except json.JSONDecodeError as e:
        debug_lines.append(f"RESULT: JSON decode error: {e}")
        _write_debug("\n".join(debug_lines))
        return {"error": "Semgrep returned invalid JSON", "results": []}
    except Exception as e:
        debug_lines.append(f"RESULT: exception: {e}")
        _write_debug("\n".join(debug_lines))
        return {"error": str(e), "results": []}


def get_semgrep_version() -> str:
    semgrep = _find_tool("semgrep")
    if not semgrep:
        return "not installed"
    try:
        r = subprocess.run(
            [semgrep, "--version"],
            capture_output=True, text=True, timeout=10,
            stdin=subprocess.PIPE,
            **_subprocess_flags()
        )
        return r.stdout.strip()
    except Exception:
        return "unknown"