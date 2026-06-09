import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QProgressBar,
    QFileDialog, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from scanner.scan_manager import ScanManager
from parser.normaliser import normalise
from database.db_manager import DBManager


class ScanWorker(QObject):
    progress = Signal(str)
    finished = Signal(list, int)
    error    = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            mgr = ScanManager()
            self.progress.emit("Running Semgrep scanner...")
            raw = mgr.run(self.path, progress_callback=lambda m: self.progress.emit(m))
            self.progress.emit("Parsing findings...")
            findings = normalise(raw.get("semgrep", {"results": []}))
            self.progress.emit(f"Found {len(findings)} raw findings. Saving to database...")
            db = DBManager()
            project_name = os.path.basename(self.path.rstrip("/\\"))
            # Fix: pass len(findings) not findings list
            scan_id = db.save_scan(project_name, self.path, len(findings))
            db.save_findings(scan_id, findings)
            self.progress.emit("Scan complete. Ready for AI validation.")
            self.finished.emit(findings, scan_id)
        except Exception as e:
            self.error.emit(str(e))


class UploadPanel(QWidget):
    scan_complete = Signal(list, int)

    def __init__(self):
        super().__init__()
        self._setup()

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

        # ── Scan card ──
        card = QFrame()
        card.setObjectName("section_card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(14)

        hdr = QHBoxLayout()
        icon = QLabel("📁")
        icon.setFixedSize(44, 44)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            "background:#EEF2FF; border-radius:10px; font-size:22px;"
            "border:1px solid #C7D2FE; color:#6c63ff;"
        )
        tc = QVBoxLayout()
        tc.setSpacing(3)
        t1 = QLabel("Scan Code")
        t1.setStyleSheet("color:#1a1a2e; font-size:18px; font-weight:bold;")
        t2 = QLabel("Select a project folder to scan for vulnerabilities using Semgrep")
        t2.setStyleSheet("color:#6B7280; font-size:12px;")
        tc.addWidget(t1)
        tc.addWidget(t2)
        hdr.addWidget(icon)
        hdr.addSpacing(12)
        hdr.addLayout(tc)
        hdr.addStretch()
        cl.addLayout(hdr)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background:#E5E7EB; max-height:1px;")
        cl.addWidget(div)

        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("No folder selected — click Browse Folder")
        self.path_edit.setReadOnly(True)
        path_row.addWidget(self.path_edit)
        browse_btn = QPushButton("📂  Browse Folder")
        browse_btn.setFixedWidth(150)
        browse_btn.setFixedHeight(38)
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(browse_btn)
        cl.addLayout(path_row)

        self.scan_btn = QPushButton("🔍  Run Semgrep Scan")
        self.scan_btn.setObjectName("scan_btn")
        self.scan_btn.setFixedHeight(50)
        self.scan_btn.setEnabled(False)
        self.scan_btn.clicked.connect(self._start)
        cl.addWidget(self.scan_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        cl.addWidget(self.progress_bar)

        self.status_lbl = QLabel("Select a folder and click Run Semgrep Scan to begin.")
        self.status_lbl.setStyleSheet("color:#6B7280; font-size:13px;")
        cl.addWidget(self.status_lbl)
        layout.addWidget(card)

        # ── Info card ──
        info = QFrame()
        info.setObjectName("section_card")
        il = QVBoxLayout(info)
        il.setContentsMargins(24, 16, 24, 16)
        il.setSpacing(10)

        it = QLabel("What happens when you scan")
        it.setStyleSheet("color:#1a1a2e; font-size:13px; font-weight:bold;")
        il.addWidget(it)

        steps = [
            ("🔍", "Semgrep scans your code using 1,000+ security rules across 30+ languages"),
            ("📋", "All raw findings are saved to the local SQLite database"),
            ("🤖", "Go to the Validate screen to run AI false positive detection"),
            ("⚡", "AI will re-classify severity for all validated true positives"),
            ("📄", "Export a full PDF report once validation is complete"),
        ]
        for emoji, text in steps:
            row = QHBoxLayout()
            row.setSpacing(10)
            e = QLabel(emoji)
            e.setFixedWidth(24)
            e.setStyleSheet("color:#6c63ff; font-size:14px;")
            t = QLabel(text)
            t.setStyleSheet("color:#374151; font-size:12px;")
            row.addWidget(e)
            row.addWidget(t)
            row.addStretch()
            il.addLayout(row)

        layout.addWidget(info)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if path:
            self.path_edit.setText(path)
            self.scan_btn.setEnabled(True)
            self.status_lbl.setText(f"Ready to scan: {os.path.basename(path)}")

    def _start(self):
        path = self.path_edit.text().strip()
        if not path or not os.path.exists(path):
            self.status_lbl.setText("Please select a valid folder first.")
            return
        self.scan_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_lbl.setText("Starting scan...")

        self._thread = QThread()
        self._worker = ScanWorker(path)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(lambda m: self.status_lbl.setText(f"⏳  {m}"))
        self._worker.finished.connect(self._done)
        self._worker.error.connect(self._err)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _done(self, findings, scan_id):
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.status_lbl.setText(
            f"✅  Scan complete — {len(findings)} raw findings detected. "
            "Go to Validate to run AI analysis."
        )
        self.scan_complete.emit(findings, scan_id)

    def _err(self, msg):
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.status_lbl.setText(f"❌  Error: {msg}")