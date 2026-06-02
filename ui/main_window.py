from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QLineEdit
)
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "SentinelAI — Intelligent SAST Validation and Severity Classification"
        )
        self.setMinimumSize(1280, 800)
        self._nav_btns = {}
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._master = QStackedWidget()
        root.addWidget(self._master)

        from ui.splash_screen import SplashScreen
        self._splash = SplashScreen(on_start=self._show_app)
        self._master.addWidget(self._splash)

        self._app_container = QWidget()
        al = QHBoxLayout(self._app_container)
        al.setContentsMargins(0, 0, 0, 0)
        al.setSpacing(0)
        al.addWidget(self._build_sidebar())

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        rl.addWidget(self._build_topbar())

        self.stack = QStackedWidget()
        rl.addWidget(self.stack)
        al.addWidget(right)
        self._master.addWidget(self._app_container)
        self._master.setCurrentIndex(0)
        self.statusBar().showMessage("SentinelAI  —  Ready")

    def _show_app(self):
        self._add_screens()
        self._switch(0)
        self._master.setCurrentIndex(1)
        # Auto-load latest results from DB on startup
        self.results_panel.refresh_latest()

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo_area = QWidget()
        logo_area.setFixedHeight(72)
        ll = QHBoxLayout(logo_area)
        ll.setContentsMargins(20, 0, 20, 0)
        shield = QLabel("🛡")
        shield.setStyleSheet("font-size:24px; color:#6c63ff;")
        shield.setFixedWidth(32)
        ll.addWidget(shield)
        nc = QVBoxLayout()
        nc.setSpacing(0)
        n1 = QLabel("SentinelAI")
        n1.setObjectName("logo_name")
        n2 = QLabel("SAST Validator")
        n2.setObjectName("logo_sub")
        nc.addWidget(n1)
        nc.addWidget(n2)
        ll.addLayout(nc)
        layout.addWidget(logo_area)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background:#2a2a45; max-height:1px;")
        layout.addWidget(div)
        layout.addSpacing(10)

        nav_items = [
            ("🏠   Dashboard",     0),
            ("</>  Scan Code",     1),
            ("🤖   Validate",      2),
            ("📊   Results",       3),
            ("📄   Export Report", 4),
        ]
        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda _, i=idx: self._switch(i))
            self._nav_btns[idx] = btn
            layout.addWidget(btn)

        layout.addStretch()

        settings_btn = QPushButton("⚙️   Settings")
        settings_btn.setObjectName("nav_btn")
        settings_btn.setCheckable(True)
        settings_btn.setFixedHeight(44)
        settings_btn.clicked.connect(lambda: self._switch(5))
        self._nav_btns[5] = settings_btn
        layout.addWidget(settings_btn)

        bc = QFrame()
        bc.setStyleSheet("QFrame{background:#252540;border-radius:10px;margin:10px;}")
        bc.setFixedHeight(100)
        bl = QVBoxLayout(bc)
        bl.setContentsMargins(14, 10, 14, 10)
        bl.setSpacing(4)
        bicon = QLabel("⚡")
        bicon.setStyleSheet("font-size:20px;")
        bt = QLabel("Scan. Validate. Classify.")
        bt.setStyleSheet("color:#ffffff;font-size:10px;font-weight:bold;background:transparent;")
        bs = QLabel("AI-powered SAST analysis")
        bs.setStyleSheet("color:#8888aa;font-size:9px;background:transparent;")
        bb = QPushButton("Start New Scan")
        bb.setStyleSheet(
            "QPushButton{background:#6c63ff;color:#ffffff;border:none;border-radius:6px;"
            "padding:4px;font-size:10px;font-weight:bold;}"
            "QPushButton:hover{background:#5a52d5;}"
        )
        bb.clicked.connect(lambda: self._switch(1))
        bl.addWidget(bicon)
        bl.addWidget(bt)
        bl.addWidget(bs)
        bl.addWidget(bb)
        layout.addWidget(bc)
        layout.addSpacing(4)
        return sidebar

    def _build_topbar(self):
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(64)
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        tc = QVBoxLayout()
        tc.setSpacing(2)
        self.page_title = QLabel("Dashboard")
        self.page_subtitle = QLabel("Overview of your scan results and AI validation metrics")
        self.page_title.setObjectName("page_title")
        self.page_subtitle.setObjectName("page_subtitle")
        tc.addWidget(self.page_title)
        tc.addWidget(self.page_subtitle)
        layout.addLayout(tc)
        layout.addStretch()

        search = QLineEdit()
        search.setObjectName("search_box")
        search.setPlaceholderText("Search anything...")
        search.setFixedWidth(240)
        layout.addWidget(search)

        notif = QPushButton("🔔")
        notif.setObjectName("icon_btn")
        layout.addWidget(notif)
        return topbar

    def _add_screens(self):
        from ui.dashboard      import DashboardScreen
        from ui.upload_panel   import UploadPanel
        from ui.validate_panel import ValidatePanel
        from ui.results_panel  import ResultsPanel
        from ui.report_panel   import ReportPanel
        from ui.settings_panel import SettingsPanel

        self.dashboard      = DashboardScreen()
        self.upload_panel   = UploadPanel()
        self.validate_panel = ValidatePanel()
        self.results_panel  = ResultsPanel()
        self.report_panel   = ReportPanel()
        self.settings_panel = SettingsPanel()

        for screen in [
            self.dashboard, self.upload_panel,
            self.validate_panel, self.results_panel,
            self.report_panel, self.settings_panel
        ]:
            self.stack.addWidget(screen)

        self.upload_panel.scan_complete.connect(self._on_scan_complete)
        self.validate_panel.validation_complete.connect(self._on_validation_complete)

        # Allow clicking a dashboard row to load that scan into validate/results
        self.dashboard.scan_selected.connect(self._on_dashboard_scan_selected)

    def _switch(self, index):
        self.stack.setCurrentIndex(index)
        for idx, btn in self._nav_btns.items():
            btn.setChecked(idx == index)
        titles = {
            0: ("Dashboard",      "Overview of your scan results and AI validation metrics"),
            1: ("Scan Code",      "Select a project folder to scan with Semgrep"),
            2: ("Validate",       "Run AI false positive detection and severity classification"),
            3: ("Results",        "View validated findings with AI verdicts"),
            4: ("Export Report",  "Generate PDF and JSON security reports"),
            5: ("Settings",       "Manage storage and application data"),
        }
        title, subtitle = titles.get(index, ("SentinelAI", ""))
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)

    def _on_scan_complete(self, findings, scan_id):
        self.validate_panel.load_findings(findings, scan_id)
        self.dashboard.refresh()
        self._switch(2)
        self.statusBar().showMessage(
            f"Scan complete — {len(findings)} raw findings. Run AI validation now."
        )

    def _on_validation_complete(self, results):
        self.results_panel.load_findings(results)
        self.dashboard.refresh()
        self._switch(3)
        tp = sum(1 for f in results if not f.is_false_positive)
        fp = len(results) - tp
        self.statusBar().showMessage(
            f"Validation complete — {tp} true positives, {fp} false positives removed"
        )

    def _on_dashboard_scan_selected(self, scan_id):
        """Load findings from a past scan when clicked on the dashboard."""
        self.results_panel.load_from_scan_id(scan_id)
        self._switch(3)
        self.statusBar().showMessage(f"Loaded scan #{scan_id} — click a finding to view details")