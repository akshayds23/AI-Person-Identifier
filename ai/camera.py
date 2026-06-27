"""
VisionAI Campus - Camera Thread
=================================
Captures frames from USB camera in a background thread.
"""

import time
import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal

from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS
from database.models import SettingsModel
from utils.logger import logger


class CameraThread(QThread):
    """Background thread for USB camera capture."""

    frame_ready = Signal(np.ndarray)
    camera_status = Signal(bool, str)
    fps_updated = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._run_flag = False
        self._paused = False

        # Load camera settings from DB or env
        self._camera_index = int(SettingsModel.get("camera_index", str(CAMERA_INDEX)))
        res = SettingsModel.get("resolution", f"{CAMERA_WIDTH}x{CAMERA_HEIGHT}")
        parts = res.split("x")
        self._width = int(parts[0]) if len(parts) == 2 else CAMERA_WIDTH
        self._height = int(parts[1]) if len(parts) == 2 else CAMERA_HEIGHT
        self._target_fps = CAMERA_FPS
        self._cap = None

    def run(self):
        self._run_flag = True
        self._connect_camera()

        frame_count = 0
        fps_start = time.time()

        while self._run_flag:
            if self._paused:
                self.msleep(100)
                continue

            if self._cap is None or not self._cap.isOpened():
                self.camera_status.emit(False, "Reconnecting...")
                self.msleep(3000)
                self._connect_camera()
                continue

            ret, frame = self._cap.read()
            if not ret:
                self.camera_status.emit(False, "Frame error")
                self.msleep(100)
                continue

            self.frame_ready.emit(frame)
            frame_count += 1

            # Calculate FPS every second
            elapsed = time.time() - fps_start
            if elapsed >= 1.0:
                self.fps_updated.emit(frame_count / elapsed)
                frame_count = 0
                fps_start = time.time()

            # Frame rate limiting
            self.msleep(max(1, int(1000 / self._target_fps) - 5))

        self._release()

    def _connect_camera(self):
        try:
            self._cap = cv2.VideoCapture(self._camera_index, cv2.CAP_DSHOW)
            if self._cap.isOpened():
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
                self._cap.set(cv2.CAP_PROP_FPS, self._target_fps)
                self.camera_status.emit(True, "Connected")
                logger.info(f"Camera {self._camera_index} connected at {self._width}x{self._height}")
            else:
                self.camera_status.emit(False, "Not found")
                logger.warning(f"Camera {self._camera_index} not found")
        except Exception as e:
            self.camera_status.emit(False, str(e))
            logger.error(f"Camera error: {e}")

    def _release(self):
        if self._cap and self._cap.isOpened():
            self._cap.release()
            logger.info("Camera released")

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._run_flag = False
        self.wait(5000)

    def update_settings(self, camera_index: int, width: int, height: int):
        self._camera_index = camera_index
        self._width = width
        self._height = height
        if self._cap:
            self._release()
            self._connect_camera()
