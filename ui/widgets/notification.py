"""
VisionAI Campus - Notification Toast Widget
=============================================
Slide-in toast notifications with auto-dismiss.
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve,
                             QPoint, QSequentialAnimationGroup)
from PySide6.QtGui import QFont


class ToastNotification(QFrame):
    """Single toast notification that slides in and auto-dismisses."""

    TYPE_CONFIG = {
        "success": {"icon": "✅", "name": "toastSuccess"},
        "warning": {"icon": "⚠️", "name": "toastWarning"},
        "error":   {"icon": "❌", "name": "toastError"},
        "info":    {"icon": "ℹ️", "name": "toastInfo"},
    }

    def __init__(self, message: str, toast_type: str = "info",
                 duration_ms: int = 3000, parent=None):
        super().__init__(parent)
        cfg = self.TYPE_CONFIG.get(toast_type, self.TYPE_CONFIG["info"])
        self.setObjectName(cfg["name"])
        self.setFixedHeight(50)
        self.setMinimumWidth(300)
        self.setMaximumWidth(450)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)

        icon = QLabel(cfg["icon"])
        icon.setStyleSheet("background: transparent; font-size: 16px;")
        layout.addWidget(icon)

        msg = QLabel(message)
        msg.setStyleSheet("background: transparent; color: #f1f5f9; font-size: 13px;")
        msg.setWordWrap(True)
        layout.addWidget(msg, 1)

        # Auto dismiss
        QTimer.singleShot(duration_ms, self._fade_out)

    def _fade_out(self):
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(300)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.finished.connect(self.deleteLater)
        self._anim = anim  # prevent GC
        anim.start()


class NotificationManager:
    """
    Singleton toast notification manager.
    
    Usage:
        NotificationManager.get_instance().show("Attendance saved!", "success")
    """

    _instance = None

    def __init__(self):
        self._parent = None
        self._toasts = []
        self._y_offset = 60

    @classmethod
    def get_instance(cls) -> "NotificationManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_parent(self, parent):
        self._parent = parent

    def show(self, message: str, toast_type: str = "info", duration_ms: int = 3000):
        if not self._parent:
            return
        toast = ToastNotification(message, toast_type, duration_ms, self._parent)
        toast.show()

        # Position at top-right
        pw = self._parent.width()
        x = pw - toast.width() - 20
        y = self._y_offset + len(self._toasts) * 60
        toast.move(x, y)

        self._toasts.append(toast)
        toast.destroyed.connect(lambda: self._remove_toast(toast))

    def _remove_toast(self, toast):
        if toast in self._toasts:
            self._toasts.remove(toast)
            self._reposition()

    def _reposition(self):
        if not self._parent:
            return
        pw = self._parent.width()
        for i, t in enumerate(self._toasts):
            x = pw - t.width() - 20
            y = self._y_offset + i * 60
            t.move(x, y)
