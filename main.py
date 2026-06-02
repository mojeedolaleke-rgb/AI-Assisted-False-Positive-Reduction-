import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from dotenv import load_dotenv

load_dotenv()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SentinelAI")
    app.setOrganizationName("University of Roehampton")

    # Apply theme
    qss_path = os.path.join(os.path.dirname(__file__), "styles", "theme.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())

    # Init DB
    from database.db_manager import DBManager
    db = DBManager()
    db.init_db()

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
