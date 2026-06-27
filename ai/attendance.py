"""
VisionAI Campus - AI Attendance Engine
========================================
Orchestrates camera → detection → recognition → attendance pipeline.
"""

import time
import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal

from config import (AI_PROCESS_EVERY_N_FRAMES, RECOGNITION_COOLDOWN,
                     SNAPSHOTS_DIR)
from ai.camera import CameraThread
from ai.detection import PersonDetector
from ai.recognition import FaceRecognizer
from ai.tracker import CentroidTracker, LineCrossingCounter
from database.models import AttendanceModel, VisitorModel
from utils.helpers import generate_snapshot_filename
from utils.logger import logger


class AttendanceEngine(QThread):
    """
    Main AI pipeline orchestrator.
    
    Receives frames from CameraThread, processes them through
    YOLO detection → InsightFace recognition → attendance marking.
    """

    # Signals
    frame_processed = Signal(np.ndarray)     # annotated frame
    person_detected = Signal(int)             # person count
    student_recognized = Signal(int, str, float)  # id, name, confidence
    attendance_marked = Signal(str, str)      # name, time
    unknown_visitor = Signal(str)             # snapshot path
    visitor_count_updated = Signal(int, int, int)  # in, out, occupancy
    fps_updated = Signal(float)
    camera_status = Signal(bool, str)
    ai_status = Signal(str)                   # status message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._paused = False

        # AI Components
        self._camera = CameraThread()
        self._detector = PersonDetector()
        self._recognizer = FaceRecognizer()
        self._tracker = CentroidTracker()
        self._counter = LineCrossingCounter()

        # Cooldown: prevent re-detecting same student
        self._last_recognition: dict = {}  # student_id -> timestamp
        self._frame_count = 0
        self._process_interval = AI_PROCESS_EVERY_N_FRAMES

        # Frame buffer
        self._current_frame = None

        # Connect camera signals
        self._camera.frame_ready.connect(self._on_frame)
        self._camera.camera_status.connect(self.camera_status.emit)
        self._camera.fps_updated.connect(self.fps_updated.emit)

    def load_models(self) -> bool:
        """Load all AI models. Call before start()."""
        self.ai_status.emit("Loading YOLO model...")
        if not self._detector.load():
            self.ai_status.emit("YOLO model failed to load")
            return False

        self.ai_status.emit("Loading InsightFace model...")
        if not self._recognizer.load():
            self.ai_status.emit("InsightFace failed to load")
            return False

        self.ai_status.emit("AI models loaded")
        return True

    def start(self, priority=QThread.NormalPriority):
        """Start the AI pipeline."""
        self._running = True
        self._paused = False
        self._camera.start()
        super().start(priority)
        logger.info("Attendance engine started")

    def run(self):
        """Main processing loop."""
        while self._running:
            if self._paused or self._current_frame is None:
                self.msleep(50)
                continue

            frame = self._current_frame.copy()
            self._current_frame = None
            self._frame_count += 1

            # Only process every N frames for performance
            if self._frame_count % self._process_interval != 0:
                self.frame_processed.emit(frame)
                continue

            try:
                self._process_frame(frame)
            except Exception as e:
                logger.error(f"Pipeline error: {e}")

    def _on_frame(self, frame: np.ndarray):
        """Receive frame from camera thread."""
        self._current_frame = frame

    def _process_frame(self, frame: np.ndarray):
        """Full AI pipeline on a single frame."""
        # 1. Person Detection (YOLO)
        detections = self._detector.detect(frame)
        self.person_detected.emit(len(detections))

        # 2. Update tracker & counter
        objects = self._tracker.update(detections)
        in_c, out_c = self._counter.update(objects)
        self.visitor_count_updated.emit(in_c, out_c, self._counter.occupancy)

        # 3. Draw bounding boxes
        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (6, 182, 212), 2)
            label = f"Person {det.confidence:.0%}"
            cv2.putText(annotated, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (6, 182, 212), 1)

        # 4. Draw counting line
        h, w = annotated.shape[:2]
        line_y = self._counter.line_y
        cv2.line(annotated, (0, line_y), (w, line_y), (245, 158, 11), 2)
        cv2.putText(annotated, f"IN: {in_c}  OUT: {out_c}",
                    (10, line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (245, 158, 11), 2)

        # 5. Face Recognition
        if self._recognizer.is_loaded:
            for det in detections:
                x1, y1, x2, y2 = det.bbox
                person_crop = frame[max(0, y1):y2, max(0, x1):x2]

                if person_crop.size == 0:
                    continue

                faces = self._recognizer.get_faces(person_crop)
                for face in faces:
                    emb = face.embedding
                    if emb is None:
                        continue

                    sid, sname, conf = self._recognizer.recognize(emb)

                    if sid is not None:
                        # Check cooldown
                        now = time.time()
                        last = self._last_recognition.get(sid, 0)
                        if now - last < RECOGNITION_COOLDOWN:
                            continue
                        self._last_recognition[sid] = now

                        # Mark attendance
                        if AttendanceModel.mark(sid, conf):
                            time_str = time.strftime("%H:%M:%S")
                            self.student_recognized.emit(sid, sname, conf)
                            self.attendance_marked.emit(sname, time_str)

                        # Draw recognized label
                        cv2.putText(annotated, f"{sname} ({conf:.0%})",
                                    (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.6, (16, 185, 129), 2)
                    else:
                        # Unknown person — save snapshot
                        fname = generate_snapshot_filename()
                        path = SNAPSHOTS_DIR / fname
                        cv2.imwrite(str(path), person_crop)
                        VisitorModel.log_entry(
                            confidence=det.confidence,
                            snapshot_path=str(path),
                        )
                        self.unknown_visitor.emit(str(path))

        self.frame_processed.emit(annotated)

    def pause(self):
        self._paused = True
        self._camera.pause()

    def resume(self):
        self._paused = False
        self._camera.resume()

    def stop(self):
        self._running = False
        self._camera.stop()
        self.wait(5000)
        logger.info("Attendance engine stopped")

    def get_recognizer(self) -> FaceRecognizer:
        return self._recognizer

    def get_detector(self) -> PersonDetector:
        return self._detector
