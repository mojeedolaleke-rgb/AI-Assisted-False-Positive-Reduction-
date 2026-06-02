CREATE TABLE IF NOT EXISTS scans (
    scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    project_path TEXT NOT NULL,
    scan_timestamp TEXT NOT NULL,
    total_findings INTEGER DEFAULT 0,
    validated_findings INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    semgrep_version TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    finding_id TEXT PRIMARY KEY,
    scan_id INTEGER,
    cwe_id TEXT,
    title TEXT,
    severity TEXT,
    file_path TEXT,
    line_number INTEGER,
    code_snippet TEXT,
    scanner TEXT,
    rule_id TEXT,
    confidence TEXT,
    FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
);

CREATE TABLE IF NOT EXISTS validations (
    validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_id TEXT,
    is_false_positive INTEGER DEFAULT 0,
    fp_reason TEXT,
    ai_severity TEXT,
    ai_severity_reason TEXT,
    original_severity TEXT,
    validated_at TEXT,
    model_used TEXT,
    FOREIGN KEY (finding_id) REFERENCES findings(finding_id)
);
