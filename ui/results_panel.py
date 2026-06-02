from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QLineEdit, QComboBox,
    QTextEdit, QSplitter, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

SEV_STYLES = {
    "CRITICAL": ("background:#FEF2F2; color:#DC2626; border:1px solid #FECACA;"),
    "HIGH":     ("background:#FFF7ED; color:#EA580C; border:1px solid #FED7AA;"),
    "MEDIUM":   ("background:#FFFBEB; color:#D97706; border:1px solid #FDE68A;"),
    "LOW":      ("background:#EEF2FF; color:#6c63ff; border:1px solid #C7D2FE;"),
}
SEV_ACCENT = {
    "CRITICAL": "#DC2626", "HIGH": "#EA580C",
    "MEDIUM": "#D97706",   "LOW": "#6c63ff",
}


class FindingCard(QFrame):
    selected = Signal(object)

    def __init__(self, num, finding):
        super().__init__()
        self.finding = finding
        self.setCursor(Qt.PointingHandCursor)
        sev    = getattr(finding, 'ai_severity', None) or finding.severity
        accent = SEV_ACCENT.get(sev, "#6B7280")
        self.setStyleSheet(f"""
            QFrame {{
                background: #ffffff;
                border: 1px solid #E5E7EB;
                border-left: 4px solid {accent};
                border-radius: 10px;
            }}
            QFrame:hover {{ border-color: {accent}; border-left: 4px solid {accent}; }}
        """)
        self.setFixedHeight(76)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        num_lbl = QLabel(str(num))
        num_lbl.setFixedWidth(26)
        num_lbl.setStyleSheet("color:#9CA3AF; font-size:11px;")
        layout.addWidget(num_lbl)

        tc = QVBoxLayout()
        tc.setSpacing(4)
        tl = QLabel(finding.title)
        tl.setStyleSheet("color:#1a1a2e; font-size:12px; font-weight:bold;")
        short = finding.file_path
        if len(short) > 52:
            parts = short.replace("\\", "/").split("/")
            short = ".../" + "/".join(parts[-2:]) if len(parts) > 2 else short
        fl = QLabel(f"{short}  ·  Line {finding.line_number}")
        fl.setStyleSheet("color:#9CA3AF; font-size:10px;")
        tc.addWidget(tl)
        tc.addWidget(fl)
        layout.addLayout(tc, stretch=1)

        cwe = QLabel(finding.cwe_id)
        cwe.setFixedWidth(74)
        cwe.setAlignment(Qt.AlignCenter)
        cwe.setStyleSheet(
            "background:#F3F4F6; color:#374151; border-radius:5px;"
            "padding:3px 4px; font-size:10px; font-weight:bold;"
            "border:1px solid #E5E7EB;"
        )
        layout.addWidget(cwe)

        is_fp = getattr(finding, 'is_false_positive', False)
        if is_fp:
            badge = QLabel("FP Filtered")
            badge.setStyleSheet(
                "background:#F0FDF4; color:#16A34A; border-radius:5px;"
                "padding:3px 7px; font-size:10px; font-weight:bold;"
                "border:1px solid #BBF7D0;"
            )
        else:
            sev_label = getattr(finding, 'ai_severity', None) or finding.severity
            badge = QLabel(sev_label)
            badge.setStyleSheet(
                SEV_STYLES.get(sev_label,
                    "background:#F3F4F6; color:#374151; border:1px solid #E5E7EB;")
                + " border-radius:5px; padding:3px 7px; font-size:10px; font-weight:bold;"
            )
        badge.setFixedWidth(82)
        badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(badge)

    def mousePressEvent(self, event):
        self.selected.emit(self.finding)
        super().mousePressEvent(event)


def _load_findings_from_db(scan_id):
    """Load findings from DB and reconstruct Finding-like objects with validation data."""
    try:
        from database.db_manager import DBManager
        from parser.normaliser import Finding
        import uuid
        rows = DBManager().get_findings_by_scan(scan_id)
        findings = []
        for r in rows:
            f = Finding(
                finding_id=r["finding_id"],
                cwe_id=r["cwe_id"],
                title=r["title"],
                severity=r["severity"],
                file_path=r["file_path"],
                line_number=r["line_number"],
                code_snippet=r["code_snippet"] or "",
                scanner=r["scanner"],
                rule_id=r["rule_id"],
                confidence=r["confidence"],
            )
            # Attach validation fields
            f.is_false_positive = bool(r["is_false_positive"]) if r["is_false_positive"] is not None else False
            f.fp_reason = r["fp_reason"] or ""
            f.ai_severity = r["ai_severity"] or r["severity"]
            f.ai_severity_reason = r["ai_severity_reason"] or ""
            f.validated = r["fp_reason"] is not None
            findings.append(f)
        return findings
    except Exception:
        return []


class ResultsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._all = []
        self._setup()

    def load_findings(self, findings):
        self._all = findings
        self._populate(findings)

    def load_from_scan_id(self, scan_id):
        """Load and display validated findings from DB for a given scan."""
        findings = _load_findings_from_db(scan_id)
        self.load_findings(findings)

    def refresh_latest(self):
        """Load the most recent validated scan from DB on startup."""
        try:
            from database.db_manager import DBManager
            history = DBManager().get_scan_history(limit=1)
            if history:
                scan_id = history[0]["scan_id"]
                self.load_from_scan_id(scan_id)
        except Exception:
            pass

    def _setup(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setFixedHeight(56)
        hdr.setStyleSheet("background:#ffffff; border-bottom:1px solid #E5E7EB;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(24, 0, 24, 0)
        hl.setSpacing(10)
        self.title_lbl = QLabel("Validation Results")
        self.title_lbl.setStyleSheet("color:#1a1a2e; font-size:18px; font-weight:bold;")
        self.count_badge = QLabel("0 findings")
        self.count_badge.setStyleSheet(
            "background:#F3F4F6; color:#6B7280; padding:3px 10px;"
            "border-radius:10px; font-size:11px;"
        )
        reload_btn = QPushButton("↻  Reload from DB")
        reload_btn.setFixedHeight(32)
        reload_btn.setStyleSheet(
            "QPushButton { background:#EEF2FF; color:#6c63ff; border:1px solid #C7D2FE;"
            "border-radius:8px; padding:4px 14px; font-size:11px; font-weight:bold; }"
            "QPushButton:hover { background:#C7D2FE; }"
        )
        reload_btn.clicked.connect(self.refresh_latest)
        hl.addWidget(self.title_lbl)
        hl.addWidget(self.count_badge)
        hl.addStretch()
        hl.addWidget(reload_btn)
        outer.addWidget(hdr)

        # Filter bar
        fb = QWidget()
        fb.setFixedHeight(50)
        fb.setStyleSheet("background:#F8F9FC; border-bottom:1px solid #F3F4F6;")
        fbl = QHBoxLayout(fb)
        fbl.setContentsMargins(24, 0, 24, 0)
        fbl.setSpacing(10)

        self.sev_filter = QComboBox()
        self.sev_filter.addItems([
            "All", "True Positives Only", "False Positives Only",
            "CRITICAL", "HIGH", "MEDIUM", "LOW"
        ])
        self.sev_filter.setFixedWidth(180)
        self.sev_filter.setFixedHeight(34)
        self.sev_filter.currentIndexChanged.connect(self._filter)
        fbl.addWidget(self.sev_filter)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search title, CWE or file...")
        self.search.setFixedHeight(34)
        self.search.textChanged.connect(self._filter)
        fbl.addWidget(self.search, stretch=1)

        self.badges = {}
        for label, color, key in [
            ("TP", "#EF4444", "tp"),
            ("FP", "#10B981", "fp"),
        ]:
            b = QLabel(f"{label}: 0")
            r2 = int(color[1:3],16); g2 = int(color[3:5],16); b2 = int(color[5:7],16)
            b.setStyleSheet(
                f"background:rgba({r2},{g2},{b2},0.05); color:{color}; border:1px solid rgba({r2},{g2},{b2},0.2);"
                "border-radius:6px; padding:4px 10px; font-size:11px; font-weight:bold;"
            )
            self.badges[key] = b
            fbl.addWidget(b)
        outer.addWidget(fb)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left — cards
        left = QWidget()
        left.setStyleSheet("background:#F8F9FC;")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background:#F8F9FC; border:none;")

        self.cards_widget = QWidget()
        self.cards_widget.setStyleSheet("background:#F8F9FC;")
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setContentsMargins(14, 12, 14, 12)
        self.cards_layout.setSpacing(6)
        self.cards_layout.addStretch()
        scroll.setWidget(self.cards_widget)
        ll.addWidget(scroll)

        foot = QWidget()
        foot.setFixedHeight(36)
        foot.setStyleSheet("background:#ffffff; border-top:1px solid #E5E7EB;")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(16, 0, 16, 0)
        self.footer_lbl = QLabel("0 results")
        self.footer_lbl.setStyleSheet("color:#9CA3AF; font-size:11px;")
        fl.addWidget(self.footer_lbl)
        ll.addWidget(foot)
        splitter.addWidget(left)

        # Right — detail panel
        right = QWidget()
        right.setStyleSheet("background:#ffffff;")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(20, 20, 20, 20)
        rl.setSpacing(12)

        self.detail_title = QLabel("Select a finding to view AI verdict and details")
        self.detail_title.setStyleSheet("color:#9CA3AF; font-size:14px; font-weight:bold;")
        self.detail_title.setWordWrap(True)
        rl.addWidget(self.detail_title)

        self.detail_meta = QLabel("")
        self.detail_meta.setStyleSheet("color:#9CA3AF; font-size:11px;")
        rl.addWidget(self.detail_meta)

        def sec_label(text):
            l = QLabel(text)
            l.setStyleSheet("color:#374151; font-size:12px; font-weight:bold;")
            return l

        rl.addWidget(sec_label("AI Verdict"))
        self.detail_verdict = QLabel("—")
        self.detail_verdict.setWordWrap(True)
        self.detail_verdict.setMinimumHeight(70)
        self.detail_verdict.setStyleSheet(
            "background:#F9FAFB; border:1px solid #E5E7EB; border-radius:8px;"
            "padding:10px; font-size:12px; color:#374151;"
        )
        rl.addWidget(self.detail_verdict)

        rl.addWidget(sec_label("Severity Reasoning"))
        self.detail_sev = QLabel("—")
        self.detail_sev.setWordWrap(True)
        self.detail_sev.setMinimumHeight(70)
        self.detail_sev.setStyleSheet(
            "background:#F9FAFB; border:1px solid #E5E7EB; border-radius:8px;"
            "padding:10px; font-size:12px; color:#374151;"
        )
        rl.addWidget(self.detail_sev)

        rl.addWidget(sec_label("Vulnerable Code"))
        self.detail_code = QTextEdit()
        self.detail_code.setReadOnly(True)
        self.detail_code.setStyleSheet(
            "QTextEdit { background:#1e1e2e; color:#cdd6f4; border:none;"
            "border-radius:8px; padding:10px;"
            "font-family: Consolas, 'Courier New', monospace; font-size:11px; }"
        )
        self.detail_code.setMinimumHeight(160)
        rl.addWidget(self.detail_code)
        rl.addStretch()
        splitter.addWidget(right)
        splitter.setSizes([560, 440])
        outer.addWidget(splitter)

    def _populate(self, findings):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tp = sum(1 for f in self._all if not getattr(f, 'is_false_positive', False))
        fp = len(self._all) - tp
        self.badges["tp"].setText(f"TP: {tp}")
        self.badges["fp"].setText(f"FP: {fp}")
        self.count_badge.setText(f"{len(self._all)} findings")

        if not findings:
            e = QLabel("No findings match your filter\n\nRun a scan and validate first,\nor click ↻ Reload from DB")
            e.setAlignment(Qt.AlignCenter)
            e.setStyleSheet("color:#9CA3AF; font-size:13px;")
            self.cards_layout.addWidget(e, alignment=Qt.AlignCenter)
            self.footer_lbl.setText("0 results")
        else:
            for i, f in enumerate(findings, 1):
                card = FindingCard(i, f)
                card.selected.connect(self._show_detail)
                self.cards_layout.addWidget(card)
            self.footer_lbl.setText(f"Showing {len(findings)} results")
        self.cards_layout.addStretch()

    def _filter(self):
        ftype = self.sev_filter.currentText()
        q = self.search.text().lower()
        filtered = []
        for f in self._all:
            is_fp = getattr(f, 'is_false_positive', False)
            sev   = getattr(f, 'ai_severity', None) or f.severity
            if ftype == "True Positives Only"  and is_fp:       continue
            if ftype == "False Positives Only" and not is_fp:   continue
            if ftype in ["CRITICAL", "HIGH", "MEDIUM", "LOW"] and sev != ftype: continue
            if q and q not in f.title.lower() \
                 and q not in f.cwe_id.lower() \
                 and q not in f.file_path.lower():
                continue
            filtered.append(f)
        self._populate(filtered)

    def _show_detail(self, finding):
        is_fp = getattr(finding, 'is_false_positive', False)
        sev   = getattr(finding, 'ai_severity', None) or finding.severity
        fp_r  = getattr(finding, 'fp_reason', '') or ""
        sev_r = getattr(finding, 'ai_severity_reason', '') or ""

        self.detail_title.setText(finding.title)
        self.detail_title.setStyleSheet("color:#1a1a2e; font-size:14px; font-weight:bold;")
        self.detail_meta.setText(
            f"{finding.cwe_id}  ·  {finding.file_path}  ·  Line {finding.line_number}"
        )
        self.detail_meta.setStyleSheet("color:#6B7280; font-size:11px;")

        if is_fp:
            reason_text = fp_r if fp_r else "Classified as false positive by AI."
            self.detail_verdict.setText(f"FALSE POSITIVE\n\n{reason_text}")
            self.detail_verdict.setStyleSheet(
                "background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px;"
                "padding:10px; font-size:12px; color:#166534;"
            )
        else:
            reason_text = fp_r if fp_r else "Confirmed as a true vulnerability."
            self.detail_verdict.setText(
                f"TRUE POSITIVE  —  AI Severity: {sev}\n\n{reason_text}"
            )
            self.detail_verdict.setStyleSheet(
                "background:#FEF2F2; border:1px solid #FECACA; border-radius:8px;"
                "padding:10px; font-size:12px; color:#991B1B;"
            )

        if sev_r:
            self.detail_sev.setText(sev_r)
            self.detail_sev.setStyleSheet(
                "background:#F9FAFB; border:1px solid #E5E7EB; border-radius:8px;"
                "padding:10px; font-size:12px; color:#374151;"
            )
        else:
            not_validated = not getattr(finding, 'validated', False)
            msg = "Severity not yet classified — run AI validation first." if not_validated \
                  else "No severity reasoning recorded."
            self.detail_sev.setText(msg)
            self.detail_sev.setStyleSheet(
                "background:#F9FAFB; border:1px solid #E5E7EB; border-radius:8px;"
                "padding:10px; font-size:12px; color:#9CA3AF;"
            )

        self.detail_code.setPlainText(finding.code_snippet or "No code snippet available.")