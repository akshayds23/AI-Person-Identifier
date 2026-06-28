"""
VisionAI Campus - Activity Log Widget
=======================================
Scrolling notification/activity feed for dashboard.
"""

from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QScrollArea, QFrame)
from PySide6.QtCore import Qt


class ActivityItem(QFrame):
    """Single activity log entry."""

    ICONS = {
        "student": "🎓",
        "visitor": "🚶",
        "unknown": "❓",
        "camera": "📷",
        "system": "⚙️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
    }

    def __init__(self, message: str, category: str = "system",
                 timestamp: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("activityItem")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        icon = QLabel(self.ICONS.get(category, "📌"))
        icon.setFixedWidth(24)
        icon.setStyleSheet("font-size: 16px; background: transparent;")
        layout.addWidget(icon)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("background: transparent; color: #e2e8f0; font-size: 13px;")
        layout.addWidget(msg_label, 1)

        time_str = timestamp or datetime.now().strftime("%H:%M:%S")
        time_label = QLabel(time_str)
        time_label.setStyleSheet("background: transparent; color: #64748b; font-size: 11px;")
        time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(time_label)


class ActivityLog(QWidget):
    """Scrollable activity log feed."""

    def __init__(self, max_items: int = 50, parent=None):
        super().__init__(parent)
        self._max_items = max_items
        self._items = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Recent Activity")
        header.setObjectName("sectionLabel")
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.addStretch()

        scroll.setWidget(self._container)
        outer.addWidget(scroll)

    def add_entry(self, message: str, category: str = "system"):
        item = ActivityItem(message, category)
        # Insert before the stretch
        self._layout.insertWidget(self._layout.count() - 1, item)
        self._items.append(item)

        # Remove oldest if over limit
        while len(self._items) > self._max_items:
            old = self._items.pop(0)
            self._layout.removeWidget(old)
            old.deleteLater()

    def clear_log(self):
        for item in self._items:
            self._layout.removeWidget(item)
            item.deleteLater()
        self._items.clear()
