"""
VisionAI Campus - Camera View Widget
======================================
Displays live camera feed with overlay support.
"""

import cv2
import numpy as np
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap


class CameraView(QLabel):
    """
    Widget to display camera frames with bounding box overlays.
    Receives QImage or numpy frames and displays them scaled.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cameraView")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(480, 360)
        self.setText("📷  Camera Feed")
        self.setScaledContents(False)
        self._active = False

    def set_active(self, active: bool):
        self._active = active
        self.setObjectName("cameraViewActive" if active else "cameraView")
        self.style().unpolish(self)
        self.style().polish(self)

    @Slot(np.ndarray)
    def update_frame(self, frame: np.ndarray):
        """Update display with a BGR numpy frame."""
        if frame is None:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bpl = ch * w
        img = QImage(rgb.data, w, h, bpl, QImage.Format_RGB888)
        scaled = QPixmap.fromImage(img).scaled(
            self.size(), Qt.KeepAspectRatio, Qt.FastTransformation
        )
        self.setPixmap(scaled)

    @Slot(QImage)
    def update_qimage(self, image: QImage):
        """Update display with a QImage."""
        scaled = QPixmap.fromImage(image).scaled(
            self.size(), Qt.KeepAspectRatio, Qt.FastTransformation
        )
        self.setPixmap(scaled)

    def clear_feed(self):
        """Clear the camera feed and show placeholder."""
        self.clear()
        self.setText("📷  Camera Feed")
        self.set_active(False)
