import json
from datetime import datetime


def export_json(output_path: str, scan: dict, findings: list):
    def get(f, k, d=""):
        return f.get(k, d) if isinstance(f, dict) else getattr(f, k, d)

    data = {
        "report_generated": datetime.now().isoformat(),
        "tool": "SentinelAI v1.0",
        "scan": scan,
        "findings": [
            {
                "finding_id":       get(f, "finding_id"),
                "cwe_id":           get(f, "cwe_id"),
                "title":            get(f, "title"),
                "original_severity":get(f, "severity"),
                "ai_severity":      get(f, "ai_severity") or get(f, "severity"),
                "is_false_positive":bool(get(f, "is_false_positive", False)),
                "fp_reason":        get(f, "fp_reason"),
                "ai_severity_reason":get(f, "ai_severity_reason"),
                "file_path":        get(f, "file_path"),
                "line_number":      get(f, "line_number"),
                "scanner":          get(f, "scanner"),
                "rule_id":          get(f, "rule_id"),
            }
            for f in findings
        ]
    }
    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2)
