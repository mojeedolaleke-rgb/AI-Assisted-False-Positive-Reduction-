import sqlite3
import os
import sys
from datetime import datetime


def _get_app_dir() -> str:
    if getattr(sys, 'frozen', False):
        app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        app_dir = os.path.join(app_data, "SentinelAI")
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def _get_schema_path() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "database", "schema.sql")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


class DBManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conn = None
        return cls._instance

    def get_connection(self):
        if self._conn is None:
            db_path = os.path.join(_get_app_dir(), "sentinel.db")
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def init_db(self):
        conn = self.get_connection()
        with open(_get_schema_path(), "r") as f:
            conn.executescript(f.read())
        conn.commit()

    def save_scan(self, project_name, project_path, total_findings):
        conn = self.get_connection()
        cursor = conn.execute(
            """INSERT INTO scans (project_name, project_path, scan_timestamp, total_findings)
               VALUES (?, ?, ?, ?)""",
            (project_name, project_path, datetime.now().isoformat(), int(total_findings))
        )
        conn.commit()
        return cursor.lastrowid

    def save_findings(self, scan_id, findings):
        conn = self.get_connection()
        for f in findings:
            conn.execute(
                """INSERT OR REPLACE INTO findings
                   (finding_id, scan_id, cwe_id, title, severity, file_path,
                    line_number, code_snippet, rule_id, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f.finding_id, scan_id, f.cwe_id, f.title, f.severity,
                 f.file_path, f.line_number, f.code_snippet, f.rule_id,
                 getattr(f, 'confidence', 'MEDIUM'))
            )
        conn.commit()

    def update_scan_validation(self, scan_id, false_positives, validated_findings,
                                critical=0, high=0, medium=0, low=0):
        conn = self.get_connection()
        conn.execute(
            """UPDATE scans SET false_positives=?, validated_findings=?,
               critical_count=?, high_count=?, medium_count=?, low_count=?
               WHERE scan_id=?""",
            (false_positives, validated_findings, critical, high, medium, low, scan_id)
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

    def get_scan_history(self, limit=20):
        conn = self.get_connection()
        rows = conn.execute(
            "SELECT * FROM scans ORDER BY scan_timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_findings_by_scan(self, scan_id):
        """Returns findings joined with validation data."""
        conn = self.get_connection()
        rows = conn.execute(
            """SELECT f.*,
                      v.is_false_positive,
                      v.fp_reason,
                      v.ai_severity,
                      v.ai_severity_reason,
                      v.original_severity,
                      v.model_used
               FROM findings f
               LEFT JOIN validations v ON f.finding_id = v.finding_id
               WHERE f.scan_id = ?
               ORDER BY f.severity""",
            (scan_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_severity_counts(self, scan_id):
        conn = self.get_connection()
        rows = conn.execute(
            "SELECT severity, COUNT(*) as cnt FROM findings WHERE scan_id=? GROUP BY severity",
            (scan_id,)
        ).fetchall()
        return {r["severity"]: r["cnt"] for r in rows}