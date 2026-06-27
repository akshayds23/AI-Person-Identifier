"""
VisionAI Campus - Application Controller
===========================================
Central coordinator managing window navigation and AI engine lifecycle.
"""

from PySide6.QtCore import QObject, Slot

from database.db import DatabaseManager
from database.models import UserModel, SettingsModel
from ai.attendance import AttendanceEngine
from ui.login import LoginWindow
from ui.setup import SetupWizard
from ui.dashboard import DashboardWindow
from ui.registration import StudentManagementPage
from ui.attendance_view import AttendancePage
from ui.visitor_view import VisitorPage
from ui.reports import ReportsPage
from ui.settings import SettingsPage
from ui.widgets.notification import NotificationManager
from utils.logger import logger


class AppController(QObject):
    """Central application controller."""

    def __init__(self):
        super().__init__()
        self._login_window = None
        self._dashboard = None
        self._ai_engine = None

        # Initialize database
        self._db = DatabaseManager.get_instance()
        UserModel.initialize_default_admin()

        logger.info("AppController initialized")

    def start(self):
        """Launch the application (show login or setup wizard)."""
        if not SettingsModel.is_setup_complete():
            wizard = SetupWizard()
            wizard.exec()

        self._show_login()

    def _show_login(self):
        """Show the login window."""
        if self._dashboard:
            self._dashboard.close()
            self._dashboard = None

        self._login_window = LoginWindow()
        self._login_window.login_success.connect(self._on_login_success)
        self._login_window.show()

    @Slot(str, int, str)
    def _on_login_success(self, role: str, user_id: int, username: str):
        """Handle successful login."""
        logger.info(f"User logged in: {username} ({role})")

        if self._login_window:
            self._login_window.close()
            self._login_window = None

        # Create AI engine
        self._ai_engine = AttendanceEngine()

        # Create dashboard
        self._dashboard = DashboardWindow(role=role, username=username)
        self._dashboard.logout_requested.connect(self._on_logout)

        # Create pages based on role
        if role in ("admin", "teacher"):
            students_page = StudentManagementPage()
            self._dashboard.add_page("students", students_page)

        attendance_page = AttendancePage()
        self._dashboard.add_page("attendance", attendance_page)

        if role in ("admin", "security"):
            visitor_page = VisitorPage()
            self._dashboard.add_page("visitors", visitor_page)

            # Connect visitor counts
            self._ai_engine.visitor_count_updated.connect(visitor_page.update_counts)

        reports_page = ReportsPage()
        self._dashboard.add_page("reports", reports_page)

        if role == "admin":
            settings_page = SettingsPage()
            settings_page.theme_changed.connect(self._on_theme_changed)
            self._dashboard.add_page("settings", settings_page)

        # Connect AI engine to dashboard
        self._ai_engine.frame_processed.connect(
            self._dashboard.get_camera_view().update_frame
        )
        self._ai_engine.fps_updated.connect(self._dashboard.update_fps)
        self._ai_engine.camera_status.connect(self._dashboard.update_camera_status)
        self._ai_engine.attendance_marked.connect(
            lambda name, t: self._dashboard.add_activity(
                f"{name} marked present at {t}", "student"
            )
        )
        self._ai_engine.unknown_visitor.connect(
            lambda p: self._dashboard.add_activity("Unknown visitor detected", "visitor")
        )

        self._dashboard.set_ai_engine(self._ai_engine)

        # Load AI models in background (they'll be ready when user clicks Start)
        self._ai_engine.load_models()

        # Set recognizer for student page
        if role in ("admin", "teacher"):
            students_page.set_recognizer(self._ai_engine.get_recognizer())

        self._dashboard.show()

    @Slot()
    def _on_logout(self):
        """Handle logout."""
        if self._ai_engine:
            self._ai_engine.stop()
            self._ai_engine = None

        self._show_login()

    @Slot(str)
    def _on_theme_changed(self, theme: str):
        """Handle theme change from settings."""
        NotificationManager.get_instance().show(
            "Theme will apply on next launch", "info"
        )

    def shutdown(self):
        """Graceful shutdown."""
        logger.info("Application shutting down...")
        if self._ai_engine:
            self._ai_engine.stop()
        if self._db:
            self._db.close()
        logger.info("Shutdown complete")
