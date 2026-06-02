from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class DonutChart(FigureCanvasQTAgg):
    def __init__(self):
        self.fig = Figure(facecolor="#ffffff")
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(260)
        self._draw_empty()

    def _draw_empty(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor("#ffffff")
        self.fig.patch.set_facecolor("#ffffff")
        ax.pie([1], colors=["#F3F4F6"], startangle=90,
               wedgeprops=dict(width=0.55))
        ax.text(0, 0, "No\ndata", ha="center", va="center",
                color="#9CA3AF", fontsize=11, fontweight="bold")
        ax.axis("equal")
        self.fig.tight_layout(pad=0.5)
        self.draw()

    def update_chart(self, counts: dict):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor("#ffffff")
        self.fig.patch.set_facecolor("#ffffff")
        color_map = {
            "CRITICAL": "#EF4444", "HIGH": "#F97316",
            "MEDIUM": "#F59E0B",   "LOW": "#6c63ff"
        }
        labels, sizes, colors = [], [], []
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if counts.get(sev, 0) > 0:
                labels.append(f"{sev}  {counts[sev]}")
                sizes.append(counts[sev])
                colors.append(color_map[sev])
        if sizes:
            wedges, _ = ax.pie(
                sizes, colors=colors, startangle=90,
                wedgeprops=dict(width=0.55, edgecolor="#ffffff", linewidth=2)
            )
            ax.text(0, 0, str(sum(sizes)), ha="center", va="center",
                    color="#1a1a2e", fontsize=22, fontweight="bold")
            ax.legend(wedges, labels, loc="lower center",
                      bbox_to_anchor=(0.5, -0.06), ncol=2, fontsize=9,
                      frameon=False, labelcolor="#374151")
        else:
            ax.pie([1], colors=["#F3F4F6"], startangle=90,
                   wedgeprops=dict(width=0.55))
            ax.text(0, 0, "0", ha="center", va="center",
                    color="#9CA3AF", fontsize=22, fontweight="bold")
        ax.axis("equal")
        self.fig.tight_layout(pad=0.5)
        self.draw()


class MetricCard(QFrame):
    def __init__(self, icon, label, sublabel, accent):
        super().__init__()
        self.setObjectName("metric_card")
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        icon_bg = QLabel(icon)
        icon_bg.setFixedSize(50, 50)
        icon_bg.setAlignment(Qt.AlignCenter)
        r = int(accent[1:3],16); g = int(accent[3:5],16); b = int(accent[5:7],16)
        icon_bg.setStyleSheet(
            f"background:rgba({r},{g},{b},0.08); color:{accent}; border-radius:12px;"
            f"font-size:22px; border:1px solid rgba({r},{g},{b},0.19);"
        )
        layout.addWidget(icon_bg)

        tc = QVBoxLayout()
        tc.setSpacing(3)
        self.val = QLabel("0")
        self.val.setStyleSheet("color:#1a1a2e; font-size:26px; font-weight:bold;")
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#374151; font-size:12px; font-weight:bold;")
        sub = QLabel(sublabel)
        sub.setStyleSheet("color:#9CA3AF; font-size:10px;")
        tc.addWidget(self.val)
        tc.addWidget(lbl)
        tc.addWidget(sub)
        layout.addLayout(tc)
        layout.addStretch()

        self.setStyleSheet(
            f"QFrame#metric_card {{"
            f"background:#ffffff; border:1px solid #E5E7EB;"
            f"border-left:4px solid {accent}; border-radius:12px;}}"
        )

    def update_value(self, v):
        self.val.setText(str(v))


class DashboardScreen(QWidget):
    scan_selected = Signal(int)  # emits scan_id when a row is clicked

    def __init__(self):
        super().__init__()
        self._scan_ids = []
        self._setup()

    def _setup(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background:#F8F9FC; border:none;")

        content = QWidget()
        content.setStyleSheet("background:#F8F9FC;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Metric cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        self.c_scans     = MetricCard("📁", "Total Scans",     "All projects scanned",  "#6c63ff")
        self.c_total     = MetricCard("🔍", "Raw Findings",    "Before AI validation",  "#374151")
        self.c_fp        = MetricCard("✅", "False Positives", "Filtered by AI",        "#10B981")
        self.c_validated = MetricCard("⚡", "True Positives",  "Validated findings",    "#EF4444")
        for c in [self.c_scans, self.c_total, self.c_fp, self.c_validated]:
            cards_row.addWidget(c)
        layout.addLayout(cards_row)

        # Middle row
        mid = QHBoxLayout()
        mid.setSpacing(14)

        # Chart card
        chart_card = QFrame()
        chart_card.setObjectName("section_card")
        chart_card.setMinimumHeight(340)
        cl = QVBoxLayout(chart_card)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(8)
        ct = QLabel("Validated Findings by Severity")
        ct.setStyleSheet("color:#1a1a2e; font-size:14px; font-weight:bold;")
        cl.addWidget(ct)
        self.chart = DonutChart()
        cl.addWidget(self.chart)
        mid.addWidget(chart_card, stretch=4)

        # Recent scans card
        scans_card = QFrame()
        scans_card.setObjectName("section_card")
        sl = QVBoxLayout(scans_card)
        sl.setContentsMargins(16, 16, 16, 12)
        sl.setSpacing(10)

        sh = QHBoxLayout()
        st = QLabel("Recent Scans")
        st.setStyleSheet("color:#1a1a2e; font-size:14px; font-weight:bold;")
        hint = QLabel("Click a row to view results")
        hint.setStyleSheet("color:#9CA3AF; font-size:11px;")
        sh.addWidget(st)
        sh.addStretch()
        sh.addWidget(hint)
        sl.addLayout(sh)

        self.tbl = QTableWidget()
        self.tbl.setColumnCount(6)
        self.tbl.setHorizontalHeaderLabels(
            ["Project", "Date", "Total", "FP Removed", "Validated", "Status"]
        )
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setShowGrid(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setMinimumHeight(200)
        self.tbl.setCursor(Qt.PointingHandCursor)
        self.tbl.cellClicked.connect(self._on_row_clicked)
        sl.addWidget(self.tbl)

        self.empty_lbl = QLabel("\n🔍\n\nNo scans yet\nScan a project to see results here")
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        self.empty_lbl.setStyleSheet("color:#9CA3AF; font-size:13px;")
        sl.addWidget(self.empty_lbl)
        mid.addWidget(scans_card, stretch=6)
        layout.addLayout(mid)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)
        self.refresh()

    def _on_row_clicked(self, row, _col):
        if row < len(self._scan_ids):
            self.scan_selected.emit(self._scan_ids[row])

    def refresh(self):
        try:
            from database.db_manager import DBManager
            history = DBManager().get_scan_history(limit=20)
        except Exception:
            history = []

        self._scan_ids = [s["scan_id"] for s in history]

        self.c_scans.update_value(len(history))
        self.c_total.update_value(sum(s["total_findings"] for s in history))
        self.c_fp.update_value(sum(s["false_positives"] for s in history))
        self.c_validated.update_value(sum(s["validated_findings"] for s in history))

        agg = {}
        for s in history:
            for sev, key in [
                ("CRITICAL", "critical_count"), ("HIGH", "high_count"),
                ("MEDIUM", "medium_count"),     ("LOW", "low_count")
            ]:
                agg[sev] = agg.get(sev, 0) + s.get(key, 0)
        self.chart.update_chart(agg)

        has = len(history) > 0
        self.tbl.setVisible(has)
        self.empty_lbl.setVisible(not has)
        self.tbl.setRowCount(len(history))
        for row, scan in enumerate(history):
            ts = scan["scan_timestamp"][:16].replace("T", " ")
            for col, val in enumerate([
                scan["project_name"], ts,
                str(scan["total_findings"]),
                str(scan["false_positives"]),
                str(scan["validated_findings"]),
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(QBrush(QColor("#1a1a2e")))
                self.tbl.setItem(row, col, item)

            validated = scan["validated_findings"] > 0 or scan["false_positives"] > 0
            if validated:
                s_item = QTableWidgetItem("✅  Validated")
                s_item.setForeground(QBrush(QColor("#10B981")))
            else:
                s_item = QTableWidgetItem("⏳  Awaiting AI")
                s_item.setForeground(QBrush(QColor("#F59E0B")))
            self.tbl.setItem(row, 5, s_item)