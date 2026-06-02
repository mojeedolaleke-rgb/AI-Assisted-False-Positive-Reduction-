import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFileDialog, QFrame,
    QButtonGroup, QRadioButton, QMessageBox,
    QScrollArea, QComboBox
)
from PySide6.QtCore import Qt, QSettings


class ReportPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._settings = QSettings("SentinelAI", "ReportPanel")
        self._scans = []
        self._setup()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_scans()

    def _load_scans(self):
        try:
            from database.db_manager import DBManager
            self._scans = DBManager().get_scan_history(limit=50)
        except Exception:
            self._scans = []
        self.combo.clear()
        if not self._scans:
            self.combo.addItem("No scans available — run a scan first")
        else:
            for s in self._scans:
                ts = s["scan_timestamp"][:16].replace("T", " ")
                fp  = s.get("false_positives", 0)
                tp  = s.get("validated_findings", 0)
                self.combo.addItem(
                    f"{s['project_name']}  —  {tp} validated, {fp} FP removed  ({ts})"
                )

    def _default_path(self):
        saved = self._settings.value("last_dir", "")
        return (
            saved if saved and os.path.exists(saved)
            else os.path.join(os.path.expanduser("~"), "Downloads")
        )

    def _setup(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background:#F8F9FC; border:none;")

        content = QWidget()
        content.setStyleSheet("background:#F8F9FC;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # ── Section helper ──────────────────────────────────
        def section(icon, title, subtitle=None):
            card = QFrame()
            card.setObjectName("section_card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(20, 16, 20, 16)
            cl.setSpacing(12)

            hdr = QHBoxLayout()
            hdr.setSpacing(10)
            ic = QLabel(icon)
            ic.setFixedSize(36, 36)
            ic.setAlignment(Qt.AlignCenter)
            ic.setStyleSheet(
                "background:#EEF2FF; border-radius:8px; font-size:18px;"
                "border:1px solid #C7D2FE;"
            )
            tc = QVBoxLayout()
            tc.setSpacing(2)
            tl = QLabel(title)
            tl.setStyleSheet(
                "color:#1a1a2e; font-size:14px; font-weight:bold;"
            )
            tc.addWidget(tl)
            if subtitle:
                sl = QLabel(subtitle)
                sl.setStyleSheet("color:#9CA3AF; font-size:11px;")
                tc.addWidget(sl)
            hdr.addWidget(ic)
            hdr.addLayout(tc)
            hdr.addStretch()
            cl.addLayout(hdr)
            return card, cl

        # ── 1. Select Project ────────────────────────────────
        c1, l1 = section("📁", "Select Project", "Choose which scan to export")
        self.combo = QComboBox()
        self.combo.setFixedHeight(40)
        self.combo.setStyleSheet(
            "QComboBox { font-size:13px; color:#1a1a2e; }"
        )
        l1.addWidget(self.combo)
        layout.addWidget(c1)

        # ── 2. Report Format ─────────────────────────────────
        c2, l2 = section("📄", "Report Format", "Select the output format")
        self.btn_group = QButtonGroup()
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(10)

        formats = [
            ("📄", "PDF Report",   "Full report with AI verdicts and severity reasoning", 0),
            ("{}", "JSON Export",  "Structured machine-readable findings data",           1),
            ("📦", "Both",         "PDF and JSON exported together",                      2),
        ]
        for icon_f, label, desc_f, idx in formats:
            fcard = QFrame()
            fcard.setStyleSheet(
                "QFrame { background:#F9FAFB; border:1px solid #E5E7EB;"
                "border-radius:10px; }"
            )
            fcard.setFixedHeight(80)
            fcl = QVBoxLayout(fcard)
            fcl.setContentsMargins(14, 10, 14, 10)
            fcl.setSpacing(4)

            top_row = QHBoxLayout()
            top_row.setSpacing(8)
            rb = QRadioButton(f"{icon_f}  {label}")
            rb.setStyleSheet(
                "QRadioButton { color:#1a1a2e; font-size:13px; font-weight:bold; }"
                "QRadioButton::indicator { width:16px; height:16px; }"
                "QRadioButton::indicator:checked { background:#6c63ff; border-color:#6c63ff; }"
            )
            self.btn_group.addButton(rb, idx)
            if idx == 0:
                rb.setChecked(True)
            top_row.addWidget(rb)
            top_row.addStretch()
            fcl.addLayout(top_row)

            dl = QLabel(desc_f)
            dl.setStyleSheet("color:#9CA3AF; font-size:10px;")
            fcl.addWidget(dl)
            fmt_row.addWidget(fcard)

        l2.addLayout(fmt_row)
        layout.addWidget(c2)

        # ── 3. Output Folder ─────────────────────────────────
        c3, l3 = section("💾", "Output Folder", "Where to save the report")
        path_row = QHBoxLayout()
        path_row.setSpacing(10)

        self.dir_edit = QLineEdit(self._default_path())
        self.dir_edit.setFixedHeight(38)
        path_row.addWidget(self.dir_edit)

        browse_btn = QPushButton("📂  Browse")
        browse_btn.setFixedWidth(110)
        browse_btn.setFixedHeight(38)
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(browse_btn)

        dl_btn = QPushButton("⬇  Downloads")
        dl_btn.setObjectName("secondary_btn")
        dl_btn.setFixedWidth(120)
        dl_btn.setFixedHeight(38)
        dl_btn.clicked.connect(
            lambda: self.dir_edit.setText(
                os.path.join(os.path.expanduser("~"), "Downloads")
            )
        )
        path_row.addWidget(dl_btn)
        l3.addLayout(path_row)
        layout.addWidget(c3)

        # ── 4. Generate button ────────────────────────────────
        gen_card = QFrame()
        gen_card.setObjectName("section_card")
        gcl = QVBoxLayout(gen_card)
        gcl.setContentsMargins(20, 16, 20, 16)
        gcl.setSpacing(10)

        self.gen_btn = QPushButton("🚀  Generate Security Report")
        self.gen_btn.setFixedHeight(50)
        self.gen_btn.setStyleSheet("""
            QPushButton {
                background: #6c63ff; color: #ffffff;
                border: none; border-radius: 10px;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background: #5a52d5; }
            QPushButton:disabled { background: #E5E7EB; color: #9CA3AF; }
        """)
        self.gen_btn.clicked.connect(self._generate)
        gcl.addWidget(self.gen_btn)

        self.status_lbl = QLabel(
            "Select a project and choose a format, then click Generate."
        )
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("color:#9CA3AF; font-size:12px;")
        gcl.addWidget(self.status_lbl)
        layout.addWidget(gen_card)

        # ── 5. Info strip ─────────────────────────────────────
        info = QFrame()
        info.setStyleSheet(
            "QFrame { background:#EEF2FF; border:1px solid #C7D2FE; border-radius:10px; }"
        )
        il = QHBoxLayout(info)
        il.setContentsMargins(16, 10, 16, 10)
        il.setSpacing(20)
        for text in [
            "📋  PDF includes AI verdicts and severity reasoning",
            "✅  False positives listed in a separate section",
            "🔗  CWE references included for every finding",
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet("color:#374151; font-size:11px;")
            il.addWidget(lbl)
        il.addStretch()
        layout.addWidget(info)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _browse(self):
        p = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self.dir_edit.text()
        )
        if p:
            self.dir_edit.setText(p)
            self._settings.setValue("last_dir", p)

    def _generate(self):
        from database.db_manager import DBManager
        from reports.pdf_generator import generate_pdf
        from reports.json_exporter import export_json

        idx = self.combo.currentIndex()
        if not self._scans or idx < 0 or idx >= len(self._scans):
            QMessageBox.warning(self, "No Project", "Select a project first.")
            return

        scan = self._scans[idx]
        out  = self.dir_edit.text().strip() or self._default_path()
        os.makedirs(out, exist_ok=True)
        self._settings.setValue("last_dir", out)

        db   = DBManager()
        rows = db.get_findings_by_scan(scan["scan_id"])

        self.gen_btn.setEnabled(False)
        self.status_lbl.setText("⏳  Generating report...")
        self.status_lbl.setStyleSheet("color:#6c63ff; font-size:12px;")

        mode = self.btn_group.checkedId()
        generated = []
        safe = scan["project_name"].replace(" ", "_")

        try:
            if mode in (0, 2):
                path = os.path.join(out, f"SentinelAI_{safe}_Report.pdf")
                generate_pdf(path, scan, rows)
                generated.append(path)
            if mode in (1, 2):
                path = os.path.join(out, f"SentinelAI_{safe}_Report.json")
                export_json(path, scan, rows)
                generated.append(path)

            self.status_lbl.setText(f"✅  Report saved to: {out}")
            self.status_lbl.setStyleSheet("color:#10B981; font-size:12px;")
            QMessageBox.information(
                self, "Done",
                "Report generated successfully:\n\n" + "\n".join(generated)
            )
            import subprocess
            subprocess.Popen(f'explorer "{out}"')
        except Exception as e:
            self.status_lbl.setText(f"❌  Error: {e}")
            self.status_lbl.setStyleSheet("color:#EF4444; font-size:12px;")
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.gen_btn.setEnabled(True)