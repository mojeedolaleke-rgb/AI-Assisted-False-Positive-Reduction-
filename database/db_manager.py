import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(__file__), "sentinel.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


class DBManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conn = None
        return cls._instance

    def get_connection(self):
        if self._conn is None:
            self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def init_db(self):
        conn = self.get_connection()
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())
        conn.commit()

    def save_scan(self, project_name, project_path, findings) -> int:
        from collections import Counter
        counts = Counter(f.ai_severity or f.severity for f in findings)
        conn = self.get_connection()
        cur = conn.execute(
            """INSERT INTO scans
               (project_name, project_path, scan_timestamp,
                total_findings, validated_findings, false_positives,
                critical_count, high_count, medium_count, low_count)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                project_name, project_path,
                datetime.now().isoformat(),
                len(findings),
                sum(1 for f in findings if f.validated),
                sum(1 for f in findings if f.is_false_positive),
                counts.get("CRITICAL", 0),
                counts.get("HIGH", 0),
                counts.get("MEDIUM", 0),
                counts.get("LOW", 0),
            )
        )
        conn.commit()
        return cur.lastrowid

    def save_findings(self, scan_id, findings):
        conn = self.get_connection()
        for f in findings:
            conn.execute(
                """INSERT OR REPLACE INTO findings
                   (finding_id, scan_id, cwe_id, title, severity,
                    file_path, line_number, code_snippet, scanner,
                    rule_id, confidence)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (f.finding_id, scan_id, f.cwe_id, f.title, f.severity,
                 f.file_path, f.line_number, f.code_snippet,
                 f.scanner, f.rule_id, f.confidence)
            )
        conn.commit()

    def save_validation(self, finding_id, is_fp, fp_reason,
                        ai_severity, ai_severity_reason,
                        original_severity, model_used):
        conn = self.get_connection()
        conn.execute(
            """INSERT OR REPLACE INTO validations
               (finding_id, is_false_positive, fp_reason,
                ai_severity, ai_severity_reason,
                original_severity, validated_at, model_used)
               VALUES (?,?,?,?,?,?,?,?)""",
            (finding_id, 1 if is_fp else 0, fp_reason,
             ai_severity, ai_severity_reason,
             original_severity, datetime.now().isoformat(), model_used)
        )
        conn.commit()

    def get_validation(self, finding_id):
        conn = self.get_connection()
        row = conn.execute(
            "SELECT * FROM validations WHERE finding_id=? LIMIT 1",
            (finding_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_scan_history(self, limit=50):
        conn = self.get_connection()
        rows = conn.execute(
            "SELECT * FROM scans ORDER BY scan_id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_findings_by_scan(self, scan_id):
        conn = self.get_connection()
        rows = conn.execute(
            """SELECT f.*, v.is_false_positive, v.fp_reason,
                      v.ai_severity, v.ai_severity_reason
               FROM findings f
               LEFT JOIN validations v ON f.finding_id = v.finding_id
               WHERE f.scan_id = ?""",
            (scan_id,)
        ).fetchall()
        return [dict(r) for r in rows]
