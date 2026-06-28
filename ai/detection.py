"""
VisionAI Campus - YOLO Person Detection
==========================================
YOLOv11 person detection using Ultralytics.
"""

from dataclasses import dataclass
from typing import List

import numpy as np

from config import YOLO_MODEL_PATH, DETECTION_CONFIDENCE
from database.models import SettingsModel
from utils.logger import logger


@dataclass
class Detection:
    """Detected person bounding box."""
    bbox: tuple  # (x1, y1, x2, y2)
    confidence: float
    class_id: int = 0

    @property
    def center(self) -> tuple:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]


class PersonDetector:
    """YOLO-based person detection."""

    def __init__(self):
        self._model = None
        self._confidence = float(
            SettingsModel.get("detection_confidence", str(DETECTION_CONFIDENCE))
        )

    def load(self):
        """Load the YOLO model."""
        try:
            from ultralytics import YOLO
            model_path = str(YOLO_MODEL_PATH)
            logger.info(f"Loading YOLO model from: {model_path}")
            self._model = YOLO(model_path)
            logger.info("YOLO model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            return False

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect persons in a frame.
        
        Args:
            frame: BGR numpy array
        
        Returns:
            List of Detection objects (persons only)
        """
        if self._model is None:
            return []

        try:
            results = self._model.predict(
                source=frame,
                classes=[0],  # person class only
                conf=self._confidence,
                verbose=False,
            )

            detections = []
            for r in results:
                if r.boxes is None:
                    continue
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    conf = float(box.conf[0].cpu().numpy())
                    detections.append(Detection(
                        bbox=(int(x1), int(y1), int(x2), int(y2)),
                        confidence=conf,
                    ))

            return detections

        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []

    def set_confidence(self, confidence: float):
        self._confidence = confidence

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

# Adjusted YOLO confidence thresholds for indoor campus lighting
