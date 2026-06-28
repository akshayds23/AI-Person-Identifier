"""
VisionAI Campus - Sidebar Navigation Widget
=============================================
Animated sidebar with icon + text navigation buttons.
"""

from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                                QPushButton, QLabel)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont


class SidebarButton(QPushButton):
    """Navigation button with icon and text."""

    def __init__(self, icon: str, text: str, page_key: str, parent=None):
        super().__init__(f"  {icon}   {text}", parent)
        self.page_key = page_key
        self.setObjectName("sidebarButton")
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 13))

    def set_active(self, active: bool):
        self.setObjectName("sidebarButtonActive" if active else "sidebarButton")
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QFrame):
    """
    Left sidebar navigation panel.
    
    Emits page_changed(str) when a nav button is clicked.
    """

    page_changed = Signal(str)

    NAV_ITEMS = [
        ("🏠", "Dashboard", "dashboard"),
        ("🎓", "Students", "students"),
        ("📋", "Attendance", "attendance"),
        ("🚶", "Visitors", "visitors"),
        ("📊", "Reports", "reports"),
        ("⚙️", "Settings", "settings"),
    ]

    def __init__(self, role: str = "admin", parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        # App branding
        brand = QLabel("🔬 VisionAI")
        brand.setObjectName("titleLabel")
        brand.setStyleSheet("font-size: 20px; padding: 8px 4px 20px 4px; background: transparent;")
        brand.setAlignment(Qt.AlignCenter)
        layout.addWidget(brand)

        # Navigation buttons
        self._buttons: dict[str, SidebarButton] = {}
        visible_items = self._get_items_for_role(role)

        for icon, text, key in visible_items:
            btn = SidebarButton(icon, text, key)
            btn.clicked.connect(lambda checked, k=key: self._on_click(k))
            layout.addWidget(btn)
            self._buttons[key] = btn

        layout.addStretch()

        # Logout button
        logout_btn = QPushButton("  🚪   Logout")
        logout_btn.setObjectName("sidebarButton")
        logout_btn.setFixedHeight(44)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFont(QFont("Segoe UI", 13))
        logout_btn.setStyleSheet("color: #ef4444;")
        logout_btn.clicked.connect(lambda: self.page_changed.emit("logout"))
        layout.addWidget(logout_btn)

    def _get_items_for_role(self, role: str) -> list:
        if role == "admin":
            return self.NAV_ITEMS
        elif role == "teacher":
            return [i for i in self.NAV_ITEMS if i[2] in
                    ("dashboard", "attendance", "reports")]
        elif role == "security":
            return [i for i in self.NAV_ITEMS if i[2] in
                    ("dashboard", "visitors", "reports")]
        return self.NAV_ITEMS

    def _on_click(self, key: str):
        for k, btn in self._buttons.items():
            btn.set_active(k == key)
        self.page_changed.emit(key)

    def set_active_page(self, key: str):
        for k, btn in self._buttons.items():
            btn.set_active(k == key)
