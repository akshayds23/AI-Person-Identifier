"""
VisionAI Campus - Entry Point
===============================
Launches the application with theme and high-DPI support.
"""

import sys
import os
from pathlib import Path

# Ensure the project root is in path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from config import APP_NAME, STYLES_DIR, THEME
from database.models import SettingsModel
from app import AppController
from utils.logger import logger


def load_theme(app: QApplication, theme_name: str = None):
    """Load QSS theme file."""
    theme = theme_name or SettingsModel.get("theme", THEME)
    qss_path = STYLES_DIR / f"{theme}_theme.qss"

    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        logger.info(f"Theme loaded: {theme}")
    else:
        logger.warning(f"Theme file not found: {qss_path}")


def main():
    # High DPI
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    # Default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Load theme
    load_theme(app)

    # Start app controller
    controller = AppController()
    controller.start()

    # Graceful exit
    exit_code = app.exec()
    controller.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

# Ready for deployment. Production build config.
