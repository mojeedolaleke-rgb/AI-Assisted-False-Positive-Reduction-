import os
from scanner.semgrep_runner import run_semgrep, get_semgrep_version


class ScanManager:
    def __init__(self):
        self.semgrep_version = get_semgrep_version()

    def run(self, target_path: str, progress_callback=None) -> dict:
        if not os.path.exists(target_path):
            return {"semgrep": {"results": []}, "error": f"Path not found: {target_path}"}

        if progress_callback:
            progress_callback("Running Semgrep scanner...")

        semgrep_result = run_semgrep(target_path)

        if progress_callback:
            progress_callback("Scan complete. Parsing findings...")

        return {"semgrep": semgrep_result}
