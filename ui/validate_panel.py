from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QProgressBar, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QColor, QBrush


class ValidationWorker(QObject):
    progress = Signal(str, int, int)
    finished = Signal(list)
    error    = Signal(str)

    def __init__(self, findings, scan_id):
        super().__init__()
        self.findings = findings
        self.scan_id  = scan_id

    def run(self):
        try:
            from llm.ai_classifier import validate_findings_batch

            def _progress(msg, done, total):
                self.progress.emit(msg, done, total)

            results = validate_findings_batch(
                self.findings,
                progress_callback=_progress
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class ValidatePanel(QWidget):
    validation_complete = Signal(list)

    def __init__(self):
        super().__init__()
        self._findings = []
        self._scan_id  = None
        self._setup()

    def load_findings(self, findings, scan_id):
        self._findings = findings
        self._scan_id  = scan_id
        self._update_summary()

    def _setup(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Header card ──
        hcard = QFrame()
        hcard.setObjectName("section_card")
        hl = QVBoxLayout(hcard)
        hl.setContentsMargins(24, 18, 24, 18)
        hl.setSpacing(14)

        top = QHBoxLayout()
        icon = QLabel("🤖")
        icon.setFixedSize(44, 44)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            "background:#EEF2FF; border-radius:10px; font-size:22px;"
            "border:1px solid #C7D2FE; color:#6c63ff;"
        )
        tc = QVBoxLayout()
        tc.setSpacing(3)
        t1 = QLabel("AI Validation Engine")
        t1.setStyleSheet("color:#1a1a2e; font-size:17px; font-weight:bold;")
        t2 = QLabel(
            "GPT-4 analyses each finding — determines true positive or false positive, "
            "then re-classifies severity"
        )
        t2.setStyleSheet("color:#6B7280; font-size:12px;")
        t2.setWordWrap(True)
        tc.addWidget(t1)
        tc.addWidget(t2)
        top.addWidget(icon)
        top.addSpacing(12)
        top.addLayout(tc)
        top.addStretch()
        hl.addLayout(top)

        # Stats
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self._stat_cards = {}
        for key, label, color in [
            ("total",   "Raw Findings",    "#6c63ff"),
            ("fp",      "False Positives", "#10B981"),
            ("tp",      "True Positives",  "#EF4444"),
            ("fp_rate", "FP Rate",         "#F59E0B"),
        ]:
            sc = QFrame()
            r = int(color[1:3],16); g = int(color[3:5],16); b = int(color[5:7],16)
            sc.setStyleSheet(
                f"QFrame {{ background:rgba({r},{g},{b},0.05); border:1px solid rgba({r},{g},{b},0.2); "
                "border-radius:10px; }}"
            )
            sc.setFixedHeight(72)
            scl = QVBoxLayout(sc)
            scl.setContentsMargins(16, 8, 16, 8)
            scl.setSpacing(3)
            val = QLabel("—")
            val.setStyleSheet(
                f"color:{color}; font-size:22px; font-weight:bold;"
            )
            lbl = QLabel(label)
            lbl.setStyleSheet("color:#6B7280; font-size:10px;")
            scl.addWidget(val)
            scl.addWidget(lbl)
            self._stat_cards[key] = val
            stats_row.addWidget(sc)
        hl.addLayout(stats_row)

        self.validate_btn = QPushButton("🤖  Run AI Validation")
        self.validate_btn.setObjectName("validate_btn")
        self.validate_btn.setFixedHeight(48)
        self.validate_btn.setEnabled(False)
        self.validate_btn.clicked.connect(self._start)
        hl.addWidget(self.validate_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        hl.addWidget(self.progress_bar)

        self.status_lbl = QLabel("Scan a project first, then run AI validation here.")
        self.status_lbl.setStyleSheet("color:#6B7280; font-size:13px;")
        hl.addWidget(self.status_lbl)
        layout.addWidget(hcard)

        # ── Results table card ──
        rcard = QFrame()
        rcard.setObjectName("section_card")
        rl = QVBoxLayout(rcard)
        rl.setContentsMargins(16, 16, 16, 16)
        rl.setSpacing(10)

        rt = QLabel("Validation Results")
        rt.setStyleSheet("color:#1a1a2e; font-size:14px; font-weight:bold;")
        rl.addWidget(rt)

        self.results_tbl = QTableWidget()
        self.results_tbl.setColumnCount(6)
        self.results_tbl.setHorizontalHeaderLabels(
            ["#", "Vulnerability", "CWE", "Original", "AI Verdict", "AI Severity"]
        )
        self.results_tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_tbl.verticalHeader().setVisible(False)
        self.results_tbl.setShowGrid(False)
        self.results_tbl.setAlternatingRowColors(True)
        self.results_tbl.setMinimumHeight(300)
        rl.addWidget(self.results_tbl)
        layout.addWidget(rcard)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _update_summary(self):
        total = len(self._findings)
        self._stat_cards["total"].setText(str(total))
        self._stat_cards["fp"].setText("—")
        self._stat_cards["tp"].setText("—")
        self._stat_cards["fp_rate"].setText("—")
        self.validate_btn.setEnabled(total > 0)
        if total > 0:
            self.status_lbl.setText(
                f"{total} raw findings loaded. Click Run AI Validation to analyse."
            )

    def _start(self):
        self.validate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_lbl.setText("Starting AI validation...")

        self._thread = QThread()
        self._worker = ValidationWorker(self._findings, self._scan_id)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._done)
        self._worker.error.connect(self._err)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_progress(self, msg, current, total):
        self.status_lbl.setText(f"⏳  {msg}")
        pct = int(current / total * 100) if total else 0
        self.progress_bar.setValue(pct)

    def _done(self, results):
        self.progress_bar.setVisible(False)
        self.validate_btn.setEnabled(True)

        fp_count = sum(1 for f in results if f.is_false_positive)
        tp_count = len(results) - fp_count
        fp_rate  = f"{fp_count/len(results)*100:.1f}%" if results else "0%"

        self._stat_cards["fp"].setText(str(fp_count))
        self._stat_cards["tp"].setText(str(tp_count))
        self._stat_cards["fp_rate"].setText(fp_rate)
        self.status_lbl.setText(
            f"✅  Done — {tp_count} true positives, "
            f"{fp_count} false positives removed ({fp_rate} FP rate)"
        )

        sev_colors = {
            "CRITICAL": "#EF4444", "HIGH": "#F97316",
            "MEDIUM": "#F59E0B",   "LOW": "#6c63ff"
        }
        self.results_tbl.setRowCount(len(results))
        for row, f in enumerate(results):
            for col, val in enumerate([str(row+1), f.title, f.cwe_id, f.severity]):
                item = QTableWidgetItem(val)
                item.setForeground(QBrush(QColor("#1a1a2e")))
                self.results_tbl.setItem(row, col, item)

            if f.is_false_positive:
                verdict = QTableWidgetItem("✅  False Positive")
                verdict.setForeground(QBrush(QColor("#10B981")))
            else:
                verdict = QTableWidgetItem("⚠️  True Positive")
                verdict.setForeground(QBrush(QColor("#EF4444")))
            self.results_tbl.setItem(row, 4, verdict)

            ai_sev = f.ai_severity or f.severity
            sev_item = QTableWidgetItem(ai_sev)
            sev_item.setForeground(QBrush(QColor(sev_colors.get(ai_sev, "#6B7280"))))
            self.results_tbl.setItem(row, 5, sev_item)

        # Update DB
        if self._scan_id:
            try:
                from database.db_manager import DBManager
                from collections import Counter
                db = DBManager()
                tp = [f for f in results if not f.is_false_positive]
                counts = Counter(f.ai_severity or f.severity for f in tp)
                conn = db.get_connection()
                conn.execute(
                    """UPDATE scans SET false_positives=?, validated_findings=?,
                       critical_count=?, high_count=?, medium_count=?, low_count=?
                       WHERE scan_id=?""",
                    (fp_count, tp_count,
                     counts.get("CRITICAL", 0), counts.get("HIGH", 0),
                     counts.get("MEDIUM", 0), counts.get("LOW", 0),
                     self._scan_id)
                )
                conn.commit()
            except Exception:
                pass

        self.validation_complete.emit(results)

    def _err(self, msg):
        self.progress_bar.setVisible(False)
        self.validate_btn.setEnabled(True)
        self.status_lbl.setText(f"❌  Error: {msg}")