"""
VisionAI Campus - Main Dashboard
==================================
Primary application window with sidebar navigation and stacked content.
"""

from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                                QLabel, QPushButton, QFrame, QStackedWidget,
                                QGridLayout, QStatusBar)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QFont

from config import APP_NAME, SCHOOL_NAME
from database.models import AttendanceModel, VisitorModel, StudentModel, SettingsModel
from ui.widgets.sidebar import Sidebar
from ui.widgets.stat_card import StatCard
from ui.widgets.camera_view import CameraView
from ui.widgets.activity_log import ActivityLog
from ui.widgets.notification import NotificationManager
from utils.logger import logger


class DashboardWindow(QMainWindow):
    """Main application window after login."""

    logout_requested = Signal()

    def __init__(self, role: str = "admin", username: str = "", parent=None):
        super().__init__(parent)
        self._role = role
        self._username = username

        school = SettingsModel.get("school_name", SCHOOL_NAME)
        self.setWindowTitle(f"{APP_NAME} — {school}")
        self.setMinimumSize(1200, 750)

        # Notification manager
        NotificationManager.get_instance().set_parent(self)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar(role=role)
        self._sidebar.page_changed.connect(self._on_page_changed)
        main_layout.addWidget(self._sidebar)

        # Right content area
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        # Top bar
        self._topbar = self._build_topbar(school)
        right.addWidget(self._topbar)

        # Stacked pages
        self._pages = QStackedWidget()
        self._page_map = {}

        # Build dashboard page
        self._build_dashboard_page()

        right.addWidget(self._pages, 1)
        main_layout.addLayout(right, 1)

        # Status bar
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("Ready")

        # Clock timer
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        # Stats refresh timer
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._refresh_stats)
        self._stats_timer.start(5000)

        # Set initial page
        self._sidebar.set_active_page("dashboard")

        # Reference to AI engine (set externally)
        self._ai_engine = None

    def _build_topbar(self, school: str) -> QFrame:
        bar = QFrame()
        bar.setObjectName("topBar")
        bar.setFixedHeight(56)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)

        school_label = QLabel(f"🏫  {school}")
        school_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #e2e8f0; background: transparent;")
        layout.addWidget(school_label)

        layout.addStretch()

        # AI Status
        self._ai_status = QLabel("⚪  AI: Idle")
        self._ai_status.setStyleSheet("color: #94a3b8; font-size: 13px; background: transparent;")
        layout.addWidget(self._ai_status)

        layout.addSpacing(16)

        # Camera status
        self._cam_status = QLabel("📷  Camera: —")
        self._cam_status.setStyleSheet("color: #94a3b8; font-size: 13px; background: transparent;")
        layout.addWidget(self._cam_status)

        layout.addSpacing(16)

        # Clock
        self._clock_label = QLabel("")
        self._clock_label.setStyleSheet("color: #94a3b8; font-size: 13px; background: transparent;")
        layout.addWidget(self._clock_label)

        layout.addSpacing(16)

        # User
        user_label = QLabel(f"👤  {self._username} ({self._role})")
        user_label.setStyleSheet("color: #64748b; font-size: 12px; background: transparent;")
        layout.addWidget(user_label)

        return bar

    def _build_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Stat cards row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        self._stat_visitors = StatCard("🚶", "0", "Visitors Today", "cyan")
        self._stat_present = StatCard("🎓", "0", "Students Present", "green")
        self._stat_unknown = StatCard("❓", "0", "Unknown Visitors", "amber")
        self._stat_occupancy = StatCard("🏢", "0", "Current Occupancy", "purple")

        stats_row.addWidget(self._stat_visitors)
        stats_row.addWidget(self._stat_present)
        stats_row.addWidget(self._stat_unknown)
        stats_row.addWidget(self._stat_occupancy)
        layout.addLayout(stats_row)

        # Camera + Activity row
        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        # Camera section
        cam_section = QVBoxLayout()

        cam_header = QHBoxLayout()
        cam_title = QLabel("Live Camera Feed")
        cam_title.setObjectName("sectionLabel")
        cam_header.addWidget(cam_title)
        cam_header.addStretch()

        self._fps_label = QLabel("FPS: —")
        self._fps_label.setObjectName("fpsLabel")
        cam_header.addWidget(self._fps_label)
        cam_section.addLayout(cam_header)

        self._camera_view = CameraView()
        cam_section.addWidget(self._camera_view, 1)

        # Control buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._start_btn = QPushButton("▶  Start Monitoring")
        self._start_btn.setObjectName("startButton")
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.clicked.connect(self._on_start)
        btn_row.addWidget(self._start_btn)

        self._pause_btn = QPushButton("⏸  Pause")
        self._pause_btn.setObjectName("sidebarButton")
        self._pause_btn.setFixedHeight(48)
        self._pause_btn.setCursor(Qt.PointingHandCursor)
        self._pause_btn.setEnabled(False)
        self._pause_btn.clicked.connect(self._on_pause)
        btn_row.addWidget(self._pause_btn)

        self._stop_btn = QPushButton("⏹  Stop")
        self._stop_btn.setObjectName("stopButton")
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)
        btn_row.addWidget(self._stop_btn)

        cam_section.addLayout(btn_row)
        content_row.addLayout(cam_section, 3)

        # Activity log
        self._activity_log = ActivityLog()
        content_row.addWidget(self._activity_log, 1)

        layout.addLayout(content_row, 1)

        self._pages.addWidget(page)
        self._page_map["dashboard"] = self._pages.count() - 1

    def add_page(self, key: str, widget: QWidget):
        """Register a page widget with a navigation key."""
        self._pages.addWidget(widget)
        self._page_map[key] = self._pages.count() - 1

    def set_ai_engine(self, engine):
        """Connect the AI engine to the dashboard."""
        self._ai_engine = engine

    @Slot(str)
    def _on_page_changed(self, key: str):
        if key == "logout":
            self.logout_requested.emit()
            return
        idx = self._page_map.get(key)
        if idx is not None:
            self._pages.setCurrentIndex(idx)

    def _on_start(self):
        self._start_btn.setEnabled(False)
        self._pause_btn.setEnabled(True)
        self._stop_btn.setEnabled(True)
        self._camera_view.set_active(True)
        self._ai_status.setText("🟢  AI: Running")
        self._ai_status.setStyleSheet("color: #10b981; font-size: 13px; background: transparent;")
        self._activity_log.add_entry("Monitoring started", "success")
        NotificationManager.get_instance().show("Monitoring started", "success")

        if self._ai_engine:
            self._ai_engine.start()

    def _on_pause(self):
        self._start_btn.setEnabled(True)
        self._pause_btn.setEnabled(False)
        self._ai_status.setText("🟡  AI: Paused")
        self._ai_status.setStyleSheet("color: #f59e0b; font-size: 13px; background: transparent;")
        self._activity_log.add_entry("Monitoring paused", "warning")

        if self._ai_engine:
            self._ai_engine.pause()

    def _on_stop(self):
        self._start_btn.setEnabled(True)
        self._pause_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        self._camera_view.clear_feed()
        self._ai_status.setText("⚪  AI: Idle")
        self._ai_status.setStyleSheet("color: #94a3b8; font-size: 13px; background: transparent;")
        self._activity_log.add_entry("Monitoring stopped", "system")

        if self._ai_engine:
            self._ai_engine.stop()

    def _update_clock(self):
        now = datetime.now()
        self._clock_label.setText(now.strftime("🕐  %H:%M:%S  |  %d %b %Y"))

    def _refresh_stats(self):
        try:
            att_count = AttendanceModel.get_today_count()
            vis = VisitorModel.get_today_count()

            self._stat_present.set_value(str(att_count))
            self._stat_visitors.set_value(str(vis["total"]))
            self._stat_occupancy.set_value(str(vis["inside"]))
        except Exception as e:
            logger.error(f"Stats refresh error: {e}")

    @Slot(float)
    def update_fps(self, fps: float):
        self._fps_label.setText(f"FPS: {fps:.1f}")

    @Slot(bool, str)
    def update_camera_status(self, connected: bool, msg: str):
        if connected:
            self._cam_status.setText(f"📷  Camera: Connected")
            self._cam_status.setStyleSheet("color: #10b981; font-size: 13px; background: transparent;")
        else:
            self._cam_status.setText(f"📷  Camera: {msg}")
            self._cam_status.setStyleSheet("color: #ef4444; font-size: 13px; background: transparent;")

    def add_activity(self, message: str, category: str = "system"):
        self._activity_log.add_entry(message, category)

    def get_camera_view(self) -> CameraView:
        return self._camera_view

    def closeEvent(self, event):
        if self._ai_engine:
            self._ai_engine.stop()
        event.accept()
