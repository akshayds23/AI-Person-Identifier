"""
VisionAI Campus - Stat Card Widget
====================================
Reusable glassmorphic statistics card for dashboard.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont


class StatCard(QFrame):
    """
    A glassmorphic stat card showing an icon, value, and label.
    
    Usage:
        card = StatCard("👥", "0", "Visitors Today", "cyan")
        card.set_value("42")
    """

    COLOR_MAP = {
        "cyan": "statCardCyan",
        "green": "statCardGreen",
        "purple": "statCardPurple",
        "amber": "statCardAmber",
        "red": "statCardRed",
        "default": "statCard",
    }

    def __init__(self, icon: str, value: str, label: str,
                 color: str = "default", parent=None):
        super().__init__(parent)
        obj_name = self.COLOR_MAP.get(color, "statCard")
        self.setObjectName(obj_name)
        self.setFixedHeight(130)
        self.setMinimumWidth(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        # Icon + Label row
        top_row = QHBoxLayout()
        self._icon_label = QLabel(icon)
        self._icon_label.setFont(QFont("Segoe UI Emoji", 20))
        self._icon_label.setStyleSheet("background: transparent;")
        top_row.addWidget(self._icon_label)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Value
        self._value_label = QLabel(value)
        self._value_label.setObjectName("statValue")
        self._value_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self._value_label)

        # Label
        self._text_label = QLabel(label)
        self._text_label.setObjectName("statLabel")
        self._text_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self._text_label)

    def set_value(self, value: str):
        self._value_label.setText(value)

    def set_label(self, text: str):
        self._text_label.setText(text)

    def set_icon(self, icon: str):
        self._icon_label.setText(icon)
