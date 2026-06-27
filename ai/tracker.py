"""
VisionAI Campus - Person Tracker
==================================
Centroid-based tracking and line-crossing counter.
"""

from collections import OrderedDict
from typing import Dict, Tuple, List

import numpy as np
from scipy.spatial.distance import cdist

from config import MAX_DISAPPEARED_FRAMES, TRACKER_LINE_POSITION
from database.models import SettingsModel


class CentroidTracker:
    """Simple centroid-based multi-object tracker."""

    def __init__(self):
        self._max_disappeared = int(
            SettingsModel.get("max_disappeared", str(MAX_DISAPPEARED_FRAMES))
        )
        self._next_id = 0
        self._objects: OrderedDict = OrderedDict()  # id -> centroid
        self._disappeared: Dict[int, int] = {}

    def update(self, detections: list) -> OrderedDict:
        """
        Update tracker with new detections.
        
        Args:
            detections: List of Detection objects with .center property
        
        Returns:
            OrderedDict of {id: (cx, cy)}
        """
        centroids = [d.center for d in detections]

        if len(centroids) == 0:
            # Mark all as disappeared
            for oid in list(self._disappeared.keys()):
                self._disappeared[oid] += 1
                if self._disappeared[oid] > self._max_disappeared:
                    self._deregister(oid)
            return self._objects

        input_centroids = np.array(centroids)

        if len(self._objects) == 0:
            for c in centroids:
                self._register(c)
        else:
            object_ids = list(self._objects.keys())
            object_centroids = np.array(list(self._objects.values()))

            D = cdist(object_centroids, input_centroids)

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                if D[row, col] > 100:  # max distance threshold
                    continue

                oid = object_ids[row]
                self._objects[oid] = tuple(input_centroids[col])
                self._disappeared[oid] = 0
                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(D.shape[0])) - used_rows
            unused_cols = set(range(D.shape[1])) - used_cols

            for row in unused_rows:
                oid = object_ids[row]
                self._disappeared[oid] += 1
                if self._disappeared[oid] > self._max_disappeared:
                    self._deregister(oid)

            for col in unused_cols:
                self._register(tuple(input_centroids[col]))

        return self._objects

    def _register(self, centroid: tuple):
        self._objects[self._next_id] = centroid
        self._disappeared[self._next_id] = 0
        self._next_id += 1

    def _deregister(self, object_id: int):
        del self._objects[object_id]
        del self._disappeared[object_id]

    def reset(self):
        self._objects.clear()
        self._disappeared.clear()
        self._next_id = 0


class LineCrossingCounter:
    """Counts objects crossing a virtual horizontal line."""

    def __init__(self, frame_height: int = 480):
        line_pos = float(
            SettingsModel.get("tracker_line_position", str(TRACKER_LINE_POSITION))
        )
        self._line_y = int(frame_height * line_pos)
        self._previous_positions: Dict[int, int] = {}  # id -> last y
        self._in_count = 0
        self._out_count = 0

    def update(self, objects: OrderedDict) -> Tuple[int, int]:
        """
        Check for line crossings.
        
        Returns:
            (total_in, total_out)
        """
        for oid, (cx, cy) in objects.items():
            if oid in self._previous_positions:
                prev_y = self._previous_positions[oid]
                # Crossed downward (IN)
                if prev_y < self._line_y <= cy:
                    self._in_count += 1
                # Crossed upward (OUT)
                elif prev_y > self._line_y >= cy:
                    self._out_count += 1
            self._previous_positions[oid] = cy

        # Clean up old IDs
        active_ids = set(objects.keys())
        for oid in list(self._previous_positions.keys()):
            if oid not in active_ids:
                del self._previous_positions[oid]

        return self._in_count, self._out_count

    @property
    def in_count(self) -> int:
        return self._in_count

    @property
    def out_count(self) -> int:
        return self._out_count

    @property
    def occupancy(self) -> int:
        return max(0, self._in_count - self._out_count)

    @property
    def line_y(self) -> int:
        return self._line_y

    def reset(self):
        self._in_count = 0
        self._out_count = 0
        self._previous_positions.clear()
