"""
VisionAI Campus - Setup Wizard
================================
First-run setup wizard for school configuration.
"""

import cv2
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QComboBox, QFrame,
                                QFileDialog, QStackedWidget, QProgressBar)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from database.models import SettingsModel
from config import SCHOOL_NAME, CAMERA_INDEX
from utils.logger import logger


class SetupWizard(QDialog):
    """First-run setup wizard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VisionAI Campus — Initial Setup")
        self.setFixedSize(620, 580)
        self.setStyleSheet("background-color: #0a0e1a;")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(28, 20, 28, 20)

        # Title
        title = QLabel("🔧  Initial Setup")
        title.setObjectName("titleLabel")
        title.setStyleSheet("font-size: 22px; background: transparent;")
        layout.addWidget(title)

        subtitle = QLabel("Configure your school settings. This is a one-time setup.")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setStyleSheet("background: transparent;")
        layout.addWidget(subtitle)

        # Progress
        self._progress = QProgressBar()
        self._progress.setRange(0, 3)
        self._progress.setValue(0)
        self._progress.setFixedHeight(6)
        self._progress.setTextVisible(False)
        layout.addWidget(self._progress)

        # Stacked pages
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)

        self._build_page1()
        self._build_page2()
        self._build_page3()

        # Navigation
        nav = QHBoxLayout()
        self._back_btn = QPushButton("← Back")
        self._back_btn.setFixedHeight(42)
        self._back_btn.clicked.connect(self._go_back)
        self._back_btn.setEnabled(False)
        nav.addWidget(self._back_btn)

        nav.addStretch()

        self._next_btn = QPushButton("Next →")
        self._next_btn.setObjectName("primaryButton")
        self._next_btn.setFixedHeight(42)
        self._next_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.clicked.connect(self._go_next)
        nav.addWidget(self._next_btn)

        layout.addLayout(nav)

    def _build_page1(self):
        page = QFrame()
        page.setObjectName("wizardStep")
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        layout.addWidget(QLabel("School Name"))
        self._school_name = QLineEdit(SCHOOL_NAME)
        self._school_name.setFixedHeight(42)
        layout.addWidget(self._school_name)

        layout.addWidget(QLabel("School Logo (optional)"))
        logo_row = QHBoxLayout()
        self._logo_path = QLineEdit()
        self._logo_path.setFixedHeight(42)
        self._logo_path.setPlaceholderText("Select logo image...")
        logo_row.addWidget(self._logo_path, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedHeight(42)
        browse_btn.clicked.connect(self._browse_logo)
        logo_row.addWidget(browse_btn)
        layout.addLayout(logo_row)

        layout.addStretch()
        self._stack.addWidget(page)

    def _build_page2(self):
        page = QFrame()
        page.setObjectName("wizardStep")
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Camera Source"))
        self._camera_combo = QComboBox()
        self._camera_combo.setFixedHeight(42)
        self._detect_cameras()
        layout.addWidget(self._camera_combo)

        layout.addWidget(QLabel("Resolution"))
        self._resolution_combo = QComboBox()
        self._resolution_combo.setFixedHeight(42)
        self._resolution_combo.addItems([
            "640x480 (Fast)", "800x600", "1280x720 (HD)", "1920x1080 (Full HD)"
        ])
        layout.addWidget(self._resolution_combo)

        layout.addStretch()
        self._stack.addWidget(page)

    def _build_page3(self):
        page = QFrame()
        page.setObjectName("wizardStep")
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Theme"))
        self._theme_combo = QComboBox()
        self._theme_combo.setFixedHeight(42)
        self._theme_combo.addItems(["Dark", "Light"])
        layout.addWidget(self._theme_combo)

        layout.addSpacing(20)

        ready_label = QLabel("✅  You're all set! Click 'Finish' to start.")
        ready_label.setStyleSheet(
            "color: #10b981; font-size: 15px; padding: 16px; background: transparent;"
        )
        layout.addWidget(ready_label)

        layout.addStretch()
        self._stack.addWidget(page)

    def _detect_cameras(self):
        self._camera_combo.clear()
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                self._camera_combo.addItem(f"Camera {i}", i)
                cap.release()
        if self._camera_combo.count() == 0:
            self._camera_combo.addItem("No camera found", -1)

    def _browse_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._logo_path.setText(path)

    def _go_next(self):
        idx = self._stack.currentIndex()
        if idx < self._stack.count() - 1:
            self._stack.setCurrentIndex(idx + 1)
            self._progress.setValue(idx + 1)
            self._back_btn.setEnabled(True)
            if idx + 1 == self._stack.count() - 1:
                self._next_btn.setText("✓ Finish")
        else:
            self._save_and_close()

    def _go_back(self):
        idx = self._stack.currentIndex()
        if idx > 0:
            self._stack.setCurrentIndex(idx - 1)
            self._progress.setValue(idx - 1)
            self._next_btn.setText("Next →")
            if idx - 1 == 0:
                self._back_btn.setEnabled(False)

    def _save_and_close(self):
        res_text = self._resolution_combo.currentText()
        res_map = {
            "640x480 (Fast)": "640x480",
            "800x600": "800x600",
            "1280x720 (HD)": "1280x720",
            "1920x1080 (Full HD)": "1920x1080",
        }

        settings = {
            "school_name": self._school_name.text(),
            "school_logo": self._logo_path.text(),
            "camera_index": str(self._camera_combo.currentData() or 0),
            "resolution": res_map.get(res_text, "640x480"),
            "theme": self._theme_combo.currentText().lower(),
        }

        SettingsModel.set_many(settings)
        SettingsModel.mark_setup_complete()
        logger.info("Setup wizard completed")
        self.accept()
