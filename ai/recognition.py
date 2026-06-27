"""
VisionAI Campus - Face Recognition
=====================================
InsightFace-based face recognition engine.
"""

from typing import List, Tuple, Optional
import numpy as np
from scipy.spatial.distance import cosine

from config import INSIGHTFACE_MODEL_NAME, INSIGHTFACE_MODEL_DIR, RECOGNITION_THRESHOLD
from database.models import SettingsModel, StudentModel
from utils.logger import logger


class FaceRecognizer:
    """InsightFace face recognition engine."""

    def __init__(self):
        self._app = None
        self._threshold = float(
            SettingsModel.get("recognition_threshold", str(RECOGNITION_THRESHOLD))
        )
        self._embeddings_cache: List[Tuple[int, str, np.ndarray]] = []

    def load(self) -> bool:
        """Load InsightFace models."""
        try:
            from insightface.app import FaceAnalysis
            logger.info("Loading InsightFace models...")
            self._app = FaceAnalysis(
                name=INSIGHTFACE_MODEL_NAME,
                root=str(INSIGHTFACE_MODEL_DIR.parent),
                providers=["CPUExecutionProvider"],
            )
            self._app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("InsightFace models loaded successfully")
            self.refresh_cache()
            return True
        except Exception as e:
            logger.error(f"Failed to load InsightFace: {e}")
            return False

    def refresh_cache(self):
        """Reload embeddings from database into memory cache."""
        self._embeddings_cache = StudentModel.get_all_embeddings()
        logger.info(f"Embedding cache refreshed: {len(self._embeddings_cache)} faces")

    def get_faces(self, frame: np.ndarray) -> list:
        """Detect and analyze faces in a frame."""
        if self._app is None:
            return []
        try:
            faces = self._app.get(frame)
            return faces
        except Exception as e:
            logger.error(f"Face analysis error: {e}")
            return []

    def extract_embedding(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Extract face embedding from a frame (expects a single face)."""
        faces = self.get_faces(frame)
        if faces:
            return faces[0].embedding
        return None

    def recognize(self, embedding: np.ndarray) -> Tuple[Optional[int], Optional[str], float]:
        """
        Match an embedding against the database cache.
        
        Returns:
            (student_id, student_name, confidence) or (None, None, 0.0)
        """
        if not self._embeddings_cache or embedding is None:
            return None, None, 0.0

        best_match_id = None
        best_match_name = None
        best_similarity = 0.0

        for sid, name, db_emb in self._embeddings_cache:
            try:
                sim = 1.0 - cosine(embedding, db_emb)
                if sim > best_similarity:
                    best_similarity = sim
                    best_match_id = sid
                    best_match_name = name
            except Exception:
                continue

        if best_similarity >= self._threshold:
            return best_match_id, best_match_name, best_similarity
        return None, None, best_similarity

    def register_face(self, frame: np.ndarray, student_id: int) -> bool:
        """Extract and store face embedding for a student."""
        embedding = self.extract_embedding(frame)
        if embedding is not None:
            StudentModel.update(student_id, face_embedding=embedding)
            self.refresh_cache()
            logger.info(f"Face registered for student {student_id}")
            return True
        logger.warning(f"No face found for student {student_id}")
        return False

    def set_threshold(self, threshold: float):
        self._threshold = threshold

    @property
    def is_loaded(self) -> bool:
        return self._app is not None

    @property
    def registered_count(self) -> int:
        return len(self._embeddings_cache)
