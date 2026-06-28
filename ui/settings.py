"""
VisionAI Campus - Settings Page
=================================
Application settings with persistence.
"""

import cv2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QComboBox, QSlider, QLineEdit,
                                QGroupBox, QFormLayout, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal

from database.db import DatabaseManager
from database.models import SettingsModel
from config import (CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT,
                     DETECTION_CONFIDENCE, RECOGNITION_THRESHOLD)
from ui.widgets.notification import NotificationManager
from utils.helpers import get_storage_usage, get_folder_size_mb
from utils.logger import logger


class SettingsPage(QWidget):
    """Application settings page."""

    theme_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("⚙️  Settings")
        title.setObjectName("sectionLabel")
        layout.addWidget(title)

        # Camera Settings
        cam_group = QGroupBox("Camera Settings")
        cam_layout = QFormLayout(cam_group)

        self._camera_combo = QComboBox()
        self._camera_combo.setFixedHeight(40)
        self._detect_cameras()
        cam_layout.addRow("Camera Source:", self._camera_combo)

        self._resolution_combo = QComboBox()
        self._resolution_combo.setFixedHeight(40)
        self._resolution_combo.addItems(["640x480", "800x600", "1280x720", "1920x1080"])
        cur_res = SettingsModel.get("resolution", f"{CAMERA_WIDTH}x{CAMERA_HEIGHT}")
        idx = self._resolution_combo.findText(cur_res)
        if idx >= 0:
            self._resolution_combo.setCurrentIndex(idx)
        cam_layout.addRow("Resolution:", self._resolution_combo)

        layout.addWidget(cam_group)

        # AI Settings
        ai_group = QGroupBox("AI Settings")
        ai_layout = QFormLayout(ai_group)

        det_row = QHBoxLayout()
        self._det_slider = QSlider(Qt.Horizontal)
        self._det_slider.setRange(10, 95)
        det_val = int(float(SettingsModel.get(
            "detection_confidence", str(DETECTION_CONFIDENCE))) * 100)
        self._det_slider.setValue(det_val)
        self._det_label = QLabel(f"{det_val}%")
        self._det_label.setFixedWidth(40)
        self._det_slider.valueChanged.connect(
            lambda v: self._det_label.setText(f"{v}%"))
        det_row.addWidget(self._det_slider)
        det_row.addWidget(self._det_label)
        ai_layout.addRow("Detection Confidence:", det_row)

        rec_row = QHBoxLayout()
        self._rec_slider = QSlider(Qt.Horizontal)
        self._rec_slider.setRange(30, 95)
        rec_val = int(float(SettingsModel.get(
            "recognition_threshold", str(RECOGNITION_THRESHOLD))) * 100)
        self._rec_slider.setValue(rec_val)
        self._rec_label = QLabel(f"{rec_val}%")
        self._rec_label.setFixedWidth(40)
        self._rec_slider.valueChanged.connect(
            lambda v: self._rec_label.setText(f"{v}%"))
        rec_row.addWidget(self._rec_slider)
        rec_row.addWidget(self._rec_label)
        ai_layout.addRow("Recognition Threshold:", rec_row)

        layout.addWidget(ai_group)

        # Appearance
        app_group = QGroupBox("Appearance")
        app_layout = QFormLayout(app_group)

        self._theme_combo = QComboBox()
        self._theme_combo.setFixedHeight(40)
        self._theme_combo.addItems(["dark", "light"])
        cur_theme = SettingsModel.get("theme", "dark")
        idx = self._theme_combo.findText(cur_theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        app_layout.addRow("Theme:", self._theme_combo)

        layout.addWidget(app_group)

        # Database
        db_group = QGroupBox("Database")
        db_layout = QHBoxLayout(db_group)

        backup_btn = QPushButton("📦 Backup Database")
        backup_btn.setFixedHeight(40)
        backup_btn.clicked.connect(self._backup_db)
        db_layout.addWidget(backup_btn)

        restore_btn = QPushButton("📂 Restore Database")
        restore_btn.setFixedHeight(40)
        restore_btn.clicked.connect(self._restore_db)
        db_layout.addWidget(restore_btn)

        db_layout.addStretch()
        layout.addWidget(db_group)

        # Save button
        save_row = QHBoxLayout()
        save_row.addStretch()

        save_btn = QPushButton("💾  Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.setFixedHeight(48)
        save_btn.setFixedWidth(200)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)
        save_row.addWidget(save_btn)

        layout.addLayout(save_row)
        layout.addStretch()

    def _detect_cameras(self):
        self._camera_combo.clear()
        cur = int(SettingsModel.get("camera_index", str(CAMERA_INDEX)))
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                self._camera_combo.addItem(f"Camera {i}", i)
                cap.release()
        if self._camera_combo.count() == 0:
            self._camera_combo.addItem("No camera", -1)
        # Select current
        for i in range(self._camera_combo.count()):
            if self._camera_combo.itemData(i) == cur:
                self._camera_combo.setCurrentIndex(i)
                break

    def _save_settings(self):
        settings = {
            "camera_index": str(self._camera_combo.currentData() or 0),
            "resolution": self._resolution_combo.currentText(),
            "detection_confidence": str(self._det_slider.value() / 100),
            "recognition_threshold": str(self._rec_slider.value() / 100),
            "theme": self._theme_combo.currentText(),
        }
        SettingsModel.set_many(settings)
        NotificationManager.get_instance().show("Settings saved!", "success")

        cur_theme = self._theme_combo.currentText()
        self.theme_changed.emit(cur_theme)

    def _backup_db(self):
        try:
            path = DatabaseManager.get_instance().backup()
            NotificationManager.get_instance().show(f"Backup saved: {path}", "success")
        except Exception as e:
            NotificationManager.get_instance().show(f"Backup failed: {e}", "error")

    def _restore_db(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup", "", "Database (*.db)"
        )
        if path:
            reply = QMessageBox.question(
                self, "Restore Database",
                "This will replace current data. Continue?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                if DatabaseManager.get_instance().restore(path):
                    NotificationManager.get_instance().show("Database restored", "success")
                else:
                    NotificationManager.get_instance().show("Restore failed", "error")
