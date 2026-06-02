import uuid
import os
from dataclasses import dataclass, field
from parser.cwe_mapper import (
    get_cwe_from_semgrep, get_cwe_title, get_severity_from_semgrep
)


@dataclass
class Finding:
    finding_id: str
    cwe_id: str
    title: str
    severity: str
    file_path: str
    line_number: int
    code_snippet: str
    scanner: str
    rule_id: str
    confidence: str
    # AI classification results (filled after AI processing)
    is_false_positive: bool = False
    fp_reason: str = ""
    ai_severity: str = ""
    ai_severity_reason: str = ""
    validated: bool = False


def _get_snippet(file_path: str, line: int, context: int = 5) -> str:
    try:
        if not os.path.exists(file_path):
            return ""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        start = max(0, line - context - 1)
        end = min(len(lines), line + context)
        result = []
        for i, ln in enumerate(lines[start:end], start=start + 1):
            marker = ">>>" if i == line else "   "
            result.append(f"{marker} {i:4d} | {ln.rstrip()}")
        return "\n".join(result)
    except Exception:
        return ""


def parse_semgrep(raw: dict) -> list:
    findings = []
    for item in raw.get("results", []):
        rule_id = item.get("check_id", "unknown")
        cwe_id  = get_cwe_from_semgrep(rule_id)
        raw_sev = item.get("extra", {}).get("severity", "WARNING").upper()
        severity = get_severity_from_semgrep(raw_sev)
        path = item.get("path", "")
        line = item.get("start", {}).get("line", 0)

        if cwe_id == "CWE-000":
            parts = rule_id.split(".")
            title = parts[-1].replace("-", " ").replace("_", " ").title()
        else:
            title = get_cwe_title(cwe_id)

        findings.append(Finding(
            finding_id=str(uuid.uuid4()),
            cwe_id=cwe_id,
            title=title,
            severity=severity,
            file_path=path,
            line_number=line,
            code_snippet=_get_snippet(path, line),
            scanner="semgrep",
            rule_id=rule_id,
            confidence="MEDIUM",
        ))
    return findings


def normalise(semgrep_raw: dict) -> list:
    return parse_semgrep(semgrep_raw)
