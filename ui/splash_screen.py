import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


class StaticLogo(QWidget):
    def __init__(self, logo_path, parent=None):
        super().__init__(parent)
        self.setFixedSize(110, 110)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(
                100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            lbl.setPixmap(pixmap)
        layout.addWidget(lbl)


def _feature_card(icon, title, desc):
    card = QFrame()
    card.setStyleSheet("""
        QFrame { background: #ffffff; border: 1px solid #E5E7EB; border-radius: 12px; }
        QFrame:hover { border-color: #6c63ff55; }
    """)
    card.setFixedHeight(110)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(6)
    top = QHBoxLayout()
    icon_lbl = QLabel(icon)
    icon_lbl.setFixedSize(28, 28)
    icon_lbl.setAlignment(Qt.AlignCenter)
    icon_lbl.setStyleSheet(
        "background:#EEF2FF;border-radius:7px;font-size:14px;"
        "border:1px solid #C7D2FE;"
    )
    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(
        "color:#1a1a2e;font-size:11px;font-weight:bold;background:transparent;border:none;"
    )
    top.addWidget(icon_lbl)
    top.addSpacing(8)
    top.addWidget(title_lbl)
    top.addStretch()
    layout.addLayout(top)
    desc_lbl = QLabel(desc)
    desc_lbl.setWordWrap(True)
    desc_lbl.setStyleSheet(
        "color:#6B7280;font-size:9px;background:transparent;border:none;"
    )
    layout.addWidget(desc_lbl)
    return card


class SplashScreen(QWidget):
    def __init__(self, on_start, parent=None):
        super().__init__(parent)
        self._on_start = on_start
        self._build()

    def _build(self):
        self.setStyleSheet("background:#F8F9FC;")

        # Single root layout — no scroll, everything fits the window
        root = QVBoxLayout(self)
        root.setContentsMargins(80, 16, 80, 16)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignVCenter)

        # ── Logo ─────────────────────────────────────────────────────────────
        logo_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "logo.png"
        )
        self.logo = StaticLogo(logo_path)
        root.addWidget(self.logo, alignment=Qt.AlignHCenter)
        root.addSpacing(6)

        # ── Title block ───────────────────────────────────────────────────────
        t1 = QLabel("SentinelAI")
        t1.setAlignment(Qt.AlignCenter)
        t1.setStyleSheet(
            "color:#1a1a2e;font-size:34px;font-weight:bold;background:transparent;"
        )
        t2 = QLabel("Intelligent SAST Validation and Severity Classification")
        t2.setAlignment(Qt.AlignCenter)
        t2.setStyleSheet(
            "color:#6c63ff;font-size:14px;font-weight:bold;background:transparent;"
        )
        s1 = QLabel(
            "An AI-assisted pipeline for false positive reduction "
            "and vulnerability severity classification in static analysis."
        )
        s1.setAlignment(Qt.AlignCenter)
        s1.setStyleSheet("color:#6B7280;font-size:12px;background:transparent;")

        root.addWidget(t1)
        root.addSpacing(2)
        root.addWidget(t2)
        root.addSpacing(4)
        root.addWidget(s1)
        root.addSpacing(10)

        # ── Get Started button (right under the title) ────────────────────────
        btn = QPushButton("→   Get Started")
        btn.setFixedWidth(200)
        btn.setFixedHeight(44)
        btn.setStyleSheet("""
            QPushButton {
                background: #6c63ff; color: #ffffff;
                border: none; border-radius: 22px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: #5a52d5; }
        """)
        btn.clicked.connect(self._on_start)
        root.addWidget(btn, alignment=Qt.AlignHCenter)
        root.addSpacing(14)

        # ── Divider ───────────────────────────────────────────────────────────
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background:#E5E7EB;")
        root.addWidget(div)
        root.addSpacing(12)

        # ── Feature cards ─────────────────────────────────────────────────────
        feat_lbl = QLabel("System Capabilities")
        feat_lbl.setStyleSheet(
            "color:#1a1a2e;font-size:13px;font-weight:bold;background:transparent;"
        )
        root.addWidget(feat_lbl)
        root.addSpacing(8)

        features = [
            ("🔍", "Multi-Language SAST", "Semgrep scans Python, JavaScript, Java, PHP, Go and 30+ languages using 1,000+ community rules."),
            ("🤖", "AI False Positive Filter", "GPT-4 analyses each finding and determines whether it is a true vulnerability or a false positive with reasoning."),
            ("⚡", "AI Severity Classification", "Validated findings are re-classified by AI using CVSS guidelines for accurate Critical, High, Medium, Low ratings."),
        ]

        grid_row = QHBoxLayout()
        grid_row.setSpacing(12)
        for icon, title, desc in features:
            grid_row.addWidget(_feature_card(icon, title, desc))
        root.addLayout(grid_row)
        root.addSpacing(12)

        # ── Divider ───────────────────────────────────────────────────────────
        div2 = QFrame()
        div2.setFrameShape(QFrame.HLine)
        div2.setFixedHeight(1)
        div2.setStyleSheet("background:#E5E7EB;")
        root.addWidget(div2)
        root.addSpacing(12)

        # ── Student details — centered ────────────────────────────────────────
        student_card = QFrame()
        student_card.setStyleSheet(
            "QFrame{background:#ffffff;border:1px solid #E5E7EB;border-radius:12px;}"
        )
        student_card.setFixedWidth(420)
        sc = QVBoxLayout(student_card)
        sc.setContentsMargins(24, 12, 24, 12)
        sc.setSpacing(4)

        name_lbl = QLabel("Mojeed Olaleke Salako")
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(
            "color:#1a1a2e;font-size:13px;font-weight:bold;background:transparent;border:none;"
        )
        sc.addWidget(name_lbl)
        sc.addSpacing(6)

        for key, val in [
            ("Student ID",    "A00074464"),
            ("Supervisor",    "Badis Aoun"),
            ("University",    "University of Roehampton"),
            ("Programme",     "MSc Cybersecurity"),
            ("Academic Year", "2025 to 2026"),
        ]:
            row = QHBoxLayout()
            kl = QLabel(f"{key}:")
            kl.setFixedWidth(100)
            kl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            kl.setStyleSheet("color:#9CA3AF;font-size:10px;background:transparent;border:none;")
            vl = QLabel(val)
            vl.setStyleSheet("color:#374151;font-size:10px;background:transparent;border:none;")
            row.addStretch()
            row.addWidget(kl)
            row.addSpacing(10)
            row.addWidget(vl)
            row.addStretch()
            sc.addLayout(row)

        root.addWidget(student_card, alignment=Qt.AlignHCenter)
        root.addSpacing(6)

        # ── Version footer ────────────────────────────────────────────────────
        ver = QLabel("v1.0  —  SentinelAI")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color:#D1D5DB;font-size:10px;background:transparent;")
        root.addWidget(ver)