from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QComboBox,
    QMessageBox
)
from PySide6.QtCore import Qt


class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._scans = []
        self._setup()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()

    def _refresh(self):
        try:
            from database.db_manager import DBManager
            db = DBManager()
            self._scans        = db.get_scan_history(limit=100)
            total_scans        = len(self._scans)
            total_findings     = sum(s["total_findings"]    for s in self._scans)
            total_fp           = sum(s["false_positives"]   for s in self._scans)
            total_validated    = sum(s["validated_findings"] for s in self._scans)

            self._v_scans.setText(str(total_scans))
            self._v_findings.setText(str(total_findings))
            self._v_fp.setText(str(total_fp))
            self._v_validated.setText(str(total_validated))

            self._combo.clear()
            if self._scans:
                for s in self._scans:
                    ts = s["scan_timestamp"][:16].replace("T", " ")
                    self._combo.addItem(
                        f"{s['project_name']}  ({s['total_findings']} findings · {ts})"
                    )
            else:
                self._combo.addItem("No scans available")
        except Exception as e:
            print(f"Settings refresh error: {e}")

    def _stat_card(self, attr, label, color):
        card = QFrame()
        r = int(color[1:3],16); g = int(color[3:5],16); b = int(color[5:7],16)
        card.setStyleSheet(
            f"QFrame {{ background:rgba({r},{g},{b},0.05); border:1px solid rgba({r},{g},{b},0.2);"
            "border-radius:10px; }}"
        )
        card.setFixedHeight(72)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 8, 16, 8)
        cl.setSpacing(3)
        val = QLabel("0")
        val.setStyleSheet(
            f"color:{color}; font-size:22px; font-weight:bold;"
        )
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#6B7280; font-size:10px;")
        cl.addWidget(val)
        cl.addWidget(lbl)
        setattr(self, attr, val)
        return card

    def _section_card(self, icon, title):
        card = QFrame()
        card.setObjectName("section_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        hdr = QHBoxLayout()
        hdr.setSpacing(10)
        i = QLabel(icon)
        i.setFixedSize(36, 36)
        i.setAlignment(Qt.AlignCenter)
        i.setStyleSheet(
            "background:#EEF2FF; border-radius:8px; font-size:18px;"
            "border:1px solid #C7D2FE; color:#6c63ff;"
        )
        t = QLabel(title)
        t.setStyleSheet(
            "color:#1a1a2e; font-size:15px; font-weight:bold;"
        )
        hdr.addWidget(i)
        hdr.addWidget(t)
        hdr.addStretch()
        layout.addLayout(hdr)
        return card, layout

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
        layout.setSpacing(16)

        # ── Storage card ──
        sc, sl = self._section_card("🗄️", "Storage Management")

        sub = QLabel(
            "All scan data is stored locally in a SQLite database. "
            "Nothing is sent anywhere except the OpenAI API for AI classification."
        )
        sub.setStyleSheet("color:#6B7280; font-size:12px;")
        sub.setWordWrap(True)
        sl.addWidget(sub)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        for attr, label, color in [
            ("_v_scans",     "Total Scans",     "#6c63ff"),
            ("_v_findings",  "Raw Findings",    "#374151"),
            ("_v_fp",        "False Positives", "#10B981"),
            ("_v_validated", "Validated",       "#EF4444"),
        ]:
            stats_row.addWidget(self._stat_card(attr, label, color))
        sl.addLayout(stats_row)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background:#E5E7EB; max-height:1px;")
        sl.addWidget(div)

        del_lbl = QLabel("Delete a specific project:")
        del_lbl.setStyleSheet("color:#374151; font-size:13px; font-weight:bold;")
        sl.addWidget(del_lbl)

        proj_row = QHBoxLayout()
        proj_row.setSpacing(10)
        self._combo = QComboBox()
        self._combo.setFixedHeight(38)
        proj_row.addWidget(self._combo, stretch=1)

        del_btn = QPushButton("🗑  Delete Project")
        del_btn.setFixedWidth(140)
        del_btn.setFixedHeight(38)
        del_btn.setStyleSheet("""
            QPushButton {
                background: #FEF2F2; color: #DC2626;
                border: 1px solid #FECACA; border-radius: 8px;
                font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #FEE2E2; }
        """)
        del_btn.clicked.connect(self._delete_project)
        proj_row.addWidget(del_btn)
        sl.addLayout(proj_row)

        div2 = QFrame()
        div2.setFrameShape(QFrame.HLine)
        div2.setStyleSheet("background:#E5E7EB; max-height:1px;")
        sl.addWidget(div2)

        bulk_lbl = QLabel("Bulk actions — cannot be undone:")
        bulk_lbl.setStyleSheet("color:#374151; font-size:13px; font-weight:bold;")
        sl.addWidget(bulk_lbl)

        bulk_row = QHBoxLayout()
        bulk_row.setSpacing(10)

        clear_v_btn = QPushButton("🤖  Clear Validations Only")
        clear_v_btn.setFixedHeight(38)
        clear_v_btn.setStyleSheet("""
            QPushButton {
                background: #F0FDF4; color: #16A34A;
                border: 1px solid #BBF7D0; border-radius: 8px;
                font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #DCFCE7; }
        """)
        clear_v_btn.clicked.connect(self._clear_validations)
        bulk_row.addWidget(clear_v_btn)

        clear_all_btn = QPushButton("⚠️  Clear All Data")
        clear_all_btn.setFixedHeight(38)
        clear_all_btn.setStyleSheet("""
            QPushButton {
                background: #FEF2F2; color: #DC2626;
                border: 1px solid #FECACA; border-radius: 8px;
                font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #FEE2E2; }
        """)
        clear_all_btn.clicked.connect(self._clear_all)
        bulk_row.addWidget(clear_all_btn)
        sl.addLayout(bulk_row)
        layout.addWidget(sc)

        # ── About card ──
        ac, al = self._section_card("ℹ️", "About SentinelAI")

        rows = [
            ("Application",   "SentinelAI — SAST Validation and Severity Classification"),
            ("Version",       "v1.0"),
            ("Student",       "Taiwo Victor Ayodele"),
            ("Student ID",    "A00059088"),
            ("Supervisor",    "Badis Aoun"),
            ("University",    "University of Roehampton"),
            ("Programme",     "MSc Cybersecurity"),
            ("Academic Year", "2024 to 2025"),
        ]
        for key, val in rows:
            row = QHBoxLayout()
            kl = QLabel(f"{key}:")
            kl.setFixedWidth(120)
            kl.setStyleSheet("color:#9CA3AF; font-size:12px;")
            vl = QLabel(val)
            vl.setStyleSheet("color:#374151; font-size:12px;")
            row.addWidget(kl)
            row.addWidget(vl)
            row.addStretch()
            al.addLayout(row)
        layout.addWidget(ac)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _delete_project(self):
        idx = self._combo.currentIndex()
        if not self._scans or idx < 0 or idx >= len(self._scans):
            QMessageBox.warning(self, "No Project", "No project selected.")
            return
        scan = self._scans[idx]
        if QMessageBox.question(
            self, "Delete Project",
            f"Delete all data for:\n\n{scan['project_name']}\n\nCannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        try:
            from database.db_manager import DBManager
            db = DBManager()
            conn = db.get_connection()
            sid = scan["scan_id"]
            conn.execute(
                "DELETE FROM validations WHERE finding_id IN "
                "(SELECT finding_id FROM findings WHERE scan_id=?)", (sid,)
            )
            conn.execute("DELETE FROM findings WHERE scan_id=?", (sid,))
            conn.execute("DELETE FROM scans WHERE scan_id=?", (sid,))
            conn.commit()
            QMessageBox.information(self, "Deleted", f"'{scan['project_name']}' deleted.")
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _clear_validations(self):
        if QMessageBox.question(
            self, "Clear Validations",
            "Delete all AI validation results?\nScans and findings will remain.",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        try:
            from database.db_manager import DBManager
            conn = DBManager().get_connection()
            conn.execute("DELETE FROM validations")
            conn.commit()
            QMessageBox.information(self, "Done", "AI validations cleared.")
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _clear_all(self):
        if QMessageBox.question(
            self, "Clear All Data",
            "Delete ALL scans, findings and validations?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        try:
            from database.db_manager import DBManager
            conn = DBManager().get_connection()
            conn.execute("DELETE FROM validations")
            conn.execute("DELETE FROM findings")
            conn.execute("DELETE FROM scans")
            conn.commit()
            QMessageBox.information(self, "Done", "All data cleared.")
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
