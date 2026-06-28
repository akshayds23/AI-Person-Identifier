"""
VisionAI Campus - Login Window
================================
Glassmorphic login screen with role selection.
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QLineEdit, QPushButton, QComboBox,
                                QFrame, QGraphicsOpacityEffect)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

from database.models import UserModel
from ui.widgets.loading_spinner import LoadingSpinner
from utils.logger import logger
from config import APP_NAME, APP_VERSION, SCHOOL_NAME


class LoginWindow(QMainWindow):
    """Login screen with glassmorphic card."""

    login_success = Signal(str, int, str)  # role, user_id, username

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Login")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: #0a0e1a;")

        central = QWidget()
        self.setCentralWidget(central)

        # Center the login card
        main_layout = QVBoxLayout(central)
        main_layout.setAlignment(Qt.AlignCenter)

        # Login Card
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedSize(420, 500)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(40, 40, 40, 40)

        # Logo / Title
        logo = QLabel("🔬")
        logo.setFont(QFont("Segoe UI Emoji", 40))
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("background: transparent;")
        card_layout.addWidget(logo)

        title = QLabel(APP_NAME)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; background: transparent;")
        card_layout.addWidget(title)

        school = QLabel(SCHOOL_NAME)
        school.setObjectName("subtitleLabel")
        school.setAlignment(Qt.AlignCenter)
        school.setStyleSheet("background: transparent;")
        card_layout.addWidget(school)

        card_layout.addSpacing(16)

        # Username
        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("Username")
        self._username_input.setFixedHeight(44)
        card_layout.addWidget(self._username_input)

        # Password
        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Password")
        self._password_input.setEchoMode(QLineEdit.Password)
        self._password_input.setFixedHeight(44)
        self._password_input.returnPressed.connect(self._do_login)
        card_layout.addWidget(self._password_input)

        # Role selector
        self._role_combo = QComboBox()
        self._role_combo.addItems(["Admin", "Teacher", "Security"])
        self._role_combo.setFixedHeight(44)
        card_layout.addWidget(self._role_combo)

        card_layout.addSpacing(8)

        # Login button
        self._login_btn = QPushButton("Login")
        self._login_btn.setObjectName("startButton")
        self._login_btn.setFixedHeight(48)
        self._login_btn.setCursor(Qt.PointingHandCursor)
        self._login_btn.clicked.connect(self._do_login)
        card_layout.addWidget(self._login_btn)

        # Error label
        self._error_label = QLabel("")
        self._error_label.setStyleSheet(
            "color: #ef4444; font-size: 12px; background: transparent;"
        )
        self._error_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self._error_label)

        # Spinner
        self._spinner = LoadingSpinner(30)
        self._spinner.hide()
        spinner_layout = QHBoxLayout()
        spinner_layout.setAlignment(Qt.AlignCenter)
        spinner_layout.addWidget(self._spinner)
        card_layout.addLayout(spinner_layout)

        card_layout.addStretch()

        # Version
        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet("color: #4a5568; font-size: 11px; background: transparent;")
        version.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(version)

        main_layout.addWidget(card)

    def _do_login(self):
        username = self._username_input.text().strip()
        password = self._password_input.text().strip()
        role = self._role_combo.currentText().lower()

        if not username or not password:
            self._show_error("Please enter username and password")
            return

        self._error_label.setText("")
        self._login_btn.setEnabled(False)
        self._spinner.start()

        user = UserModel.authenticate(username, password)
        self._spinner.stop()
        self._login_btn.setEnabled(True)

        if user and user["role"] == role:
            logger.info(f"Login successful: {username} ({role})")
            self.login_success.emit(role, user["user_id"], username)
        elif user:
            self._show_error(f"Access denied. You are not registered as {role}.")
            self._shake_card()
        else:
            self._show_error("Invalid username or password")
            self._shake_card()

    def _show_error(self, msg: str):
        self._error_label.setText(msg)

    def _shake_card(self):
        """Shake animation on failed login."""
        card = self.centralWidget().findChild(QFrame, "loginCard")
        if not card:
            return
        anim = QPropertyAnimation(card, b"pos")
        anim.setDuration(400)
        pos = card.pos()
        anim.setKeyValueAt(0, pos)
        anim.setKeyValueAt(0.1, pos + type(pos)(10, 0))
        anim.setKeyValueAt(0.2, pos + type(pos)(-10, 0))
        anim.setKeyValueAt(0.3, pos + type(pos)(8, 0))
        anim.setKeyValueAt(0.4, pos + type(pos)(-8, 0))
        anim.setKeyValueAt(0.5, pos + type(pos)(4, 0))
        anim.setKeyValueAt(0.6, pos)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        self._shake_anim = anim
        anim.start()
