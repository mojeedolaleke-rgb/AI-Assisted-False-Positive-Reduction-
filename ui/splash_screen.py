import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QRadialGradient, QColor, QPen, QPixmap, QFont


class GlowingLogo(QWidget):
    def __init__(self, logo_path, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 160)
        self._glow = 65.0
        self._growing = True
        self._scale = 1.0
        self._pixmap = None
        if os.path.exists(logo_path):
            self._pixmap = QPixmap(logo_path).scaled(
                110, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(30)

    def _tick(self):
        if self._growing:
            self._glow += 0.3
            if self._glow >= 80: self._growing = False
        else:
            self._glow -= 0.3
            if self._glow <= 55: self._growing = True
        self._scale = 1.0 + (self._glow - 55) / 400.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width()//2, self.height()//2
        r = int(self._glow)
        for i in range(3):
            ri = r + i*6
            alpha = max(0, 70 - i*22)
            p.setPen(QPen(QColor(108, 99, 255, alpha), 1.2))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(cx-ri, cy-ri, ri*2, ri*2)
        g = QRadialGradient(cx, cy, r)
        g.setColorAt(0, QColor(108, 99, 255, 45))
        g.setColorAt(1, QColor(108, 99, 255, 0))
        p.setBrush(g)
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx-r, cy-r, r*2, r*2)
        if self._pixmap:
            s = self._scale
            pw, ph = int(self._pixmap.width()*s), int(self._pixmap.height()*s)
            scaled = self._pixmap.scaled(pw, ph, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            p.drawPixmap(cx-pw//2, cy-ph//2, scaled)
        p.end()


def _feature_card(icon, title, desc):
    card = QFrame()
    card.setStyleSheet("""
        QFrame { background: #ffffff; border: 1px solid #E5E7EB; border-radius: 12px; }
        QFrame:hover { border-color: #6c63ff55; }
    """)
    card.setFixedHeight(120)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(6)
    top = QHBoxLayout()
    icon_lbl = QLabel(icon)
    icon_lbl.setFixedSize(32, 32)
    icon_lbl.setAlignment(Qt.AlignCenter)
    icon_lbl.setStyleSheet(
        "background:#EEF2FF;border-radius:8px;font-size:16px;"
        "border:1px solid #C7D2FE;"
    )
    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(
        "color:#1a1a2e;font-size:12px;font-weight:bold;background:transparent;border:none;"
    )
    top.addWidget(icon_lbl)
    top.addSpacing(8)
    top.addWidget(title_lbl)
    top.addStretch()
    layout.addLayout(top)
    desc_lbl = QLabel(desc)
    desc_lbl.setWordWrap(True)
    desc_lbl.setStyleSheet(
        "color:#6B7280;font-size:10px;background:transparent;border:none;"
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
        root = QHBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background:#F8F9FC;border:none;")

        page = QWidget()
        page.setStyleSheet("background:#F8F9FC;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(100, 40, 100, 40)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)

        # Top row — logo + title
        top_row = QHBoxLayout()
        top_row.setSpacing(40)
        top_row.setAlignment(Qt.AlignCenter)

        logo_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "logo.png"
        )
        self.logo = GlowingLogo(logo_path)
        top_row.addWidget(self.logo, alignment=Qt.AlignVCenter)

        title_col = QVBoxLayout()
        title_col.setSpacing(8)
        title_col.setAlignment(Qt.AlignVCenter)

        t1 = QLabel("SentinelAI")
        t1.setStyleSheet(
            "color:#1a1a2e;font-size:38px;font-weight:bold;background:transparent;"
        )
        t2 = QLabel("Intelligent SAST Validation and Severity Classification")
        t2.setStyleSheet(
            "color:#6c63ff;font-size:16px;font-weight:bold;background:transparent;"
        )
        s1 = QLabel(
            "An AI-assisted pipeline for false positive reduction\n"
            "and vulnerability severity classification in static analysis."
        )
        s1.setStyleSheet("color:#6B7280;font-size:13px;background:transparent;")
        title_col.addWidget(t1)
        title_col.addWidget(t2)
        title_col.addSpacing(6)
        title_col.addWidget(s1)
        top_row.addLayout(title_col)
        layout.addLayout(top_row)
        layout.addSpacing(32)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background:#E5E7EB;")
        layout.addWidget(div)
        layout.addSpacing(28)

        # Feature cards — top 3 only
        feat_lbl = QLabel("System Capabilities")
        feat_lbl.setStyleSheet(
            "color:#1a1a2e;font-size:15px;font-weight:bold;background:transparent;"
        )
        layout.addWidget(feat_lbl)
        layout.addSpacing(12)

        features = [
            ("🔍", "Multi-Language SAST", "Semgrep scans Python, JavaScript, Java, PHP, Go and 30+ languages using 1,000+ community rules."),
            ("🤖", "AI False Positive Filter", "GPT-4 analyses each finding and determines whether it is a true vulnerability or a false positive with reasoning."),
            ("⚡", "AI Severity Classification", "Validated findings are re-classified by AI using CVSS guidelines for accurate Critical, High, Medium, Low ratings."),
        ]

        grid_row1 = QHBoxLayout()
        grid_row1.setSpacing(12)

        for icon, title, desc in features:
            card = _feature_card(icon, title, desc)
            grid_row1.addWidget(card)

        layout.addLayout(grid_row1)
        layout.addSpacing(28)

        # Divider
        div2 = QFrame()
        div2.setFrameShape(QFrame.HLine)
        div2.setFixedHeight(1)
        div2.setStyleSheet("background:#E5E7EB;")
        layout.addWidget(div2)
        layout.addSpacing(24)

        # Bottom row
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(32)
        bottom_row.setAlignment(Qt.AlignCenter)

        # Student card
        student_card = QFrame()
        student_card.setStyleSheet(
            "QFrame{background:#ffffff;border:1px solid #E5E7EB;border-radius:12px;}"
        )
        student_card.setFixedWidth(380)
        sc = QVBoxLayout(student_card)
        sc.setContentsMargins(24, 18, 24, 18)
        sc.setSpacing(6)

        name_lbl = QLabel("Mojeed Olaleke Salako")
        name_lbl.setStyleSheet(
            "color:#1a1a2e;font-size:15px;font-weight:bold;background:transparent;border:none;"
        )
        sc.addWidget(name_lbl)
        sc.addSpacing(4)

        for key, val in [
            ("Student ID",    "A00074464"),
            ("Supervisor",    "Badis Aoun"),
            ("University",    "University of Roehampton"),
            ("Programme",     "MSc Cybersecurity"),
            ("Academic Year", "2024 to 2025"),
        ]:
            row = QHBoxLayout()
            kl = QLabel(f"{key}:")
            kl.setFixedWidth(100)
            kl.setStyleSheet("color:#9CA3AF;font-size:11px;background:transparent;border:none;")
            vl = QLabel(val)
            vl.setStyleSheet("color:#374151;font-size:11px;background:transparent;border:none;")
            row.addWidget(kl)
            row.addWidget(vl)
            row.addStretch()
            sc.addLayout(row)
        bottom_row.addWidget(student_card)

        right_col = QVBoxLayout()
        right_col.setAlignment(Qt.AlignCenter)
        right_col.setSpacing(12)

        tagline = QLabel("Scan. Validate. Classify. Report.")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet(
            "color:#9CA3AF;font-size:13px;background:transparent;"
        )
        right_col.addWidget(tagline)

        btn = QPushButton("→   Get Started")
        btn.setFixedWidth(220)
        btn.setFixedHeight(50)
        btn.setStyleSheet("""
            QPushButton {
                background: #6c63ff; color: #ffffff;
                border: none; border-radius: 25px;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background: #5a52d5; }
        """)
        btn.clicked.connect(self._on_start)
        right_col.addWidget(btn, alignment=Qt.AlignCenter)

        ver = QLabel("v1.0  —  SentinelAI")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color:#D1D5DB;font-size:10px;background:transparent;")
        right_col.addWidget(ver)
        bottom_row.addLayout(right_col)
        layout.addLayout(bottom_row)

        scroll.setWidget(page)
        root.addWidget(scroll)