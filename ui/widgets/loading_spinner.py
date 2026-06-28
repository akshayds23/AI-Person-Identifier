"""
VisionAI Campus - Loading Spinner Widget
==========================================
Animated loading indicator.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QConicalGradient


class LoadingSpinner(QWidget):
    """Circular loading spinner with gradient animation."""

    def __init__(self, size: int = 40, parent=None):
        super().__init__(parent)
        self._size = size
        self._angle = 0
        self._color = QColor("#06b6d4")
        self.setFixedSize(size, size)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.setInterval(16)  # ~60fps

    def start(self):
        self.show()
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _rotate(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(4, 4, self._size - 8, self._size - 8)
        pen = QPen()
        pen.setWidth(3)
        pen.setCapStyle(Qt.RoundCap)

        # Background circle
        pen.setColor(QColor(45, 55, 72, 80))
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)

        # Spinning arc
        pen.setColor(self._color)
        painter.setPen(pen)
        painter.drawArc(rect, int(-self._angle * 16), int(90 * 16))

        painter.end()

    def set_color(self, color: str):
        self._color = QColor(color)
