"""
VisionAI Campus - Database Manager
====================================
Thread-safe SQLite database with numpy array support.
"""

import io
import sqlite3
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

from config import DATABASE_PATH, BACKUPS_DIR
from utils.logger import logger


def _adapt_numpy_array(arr: np.ndarray) -> sqlite3.Binary:
    buf = io.BytesIO()
    np.save(buf, arr)
    buf.seek(0)
    return sqlite3.Binary(buf.read())


def _convert_numpy_array(data: bytes) -> np.ndarray:
    buf = io.BytesIO(data)
    buf.seek(0)
    return np.load(buf, allow_pickle=False)


sqlite3.register_adapter(np.ndarray, _adapt_numpy_array)
sqlite3.register_converter("NPARRAY", _convert_numpy_array)


class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        raise RuntimeError("Use DatabaseManager.get_instance()")

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = object.__new__(cls)
                    inst._init_db()
                    cls._instance = inst
        return cls._instance

    def _init_db(self):
        self._db_path = DATABASE_PATH
        self._db_lock = threading.Lock()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing database at: {self._db_path}")

        self._connection = sqlite3.connect(
            str(self._db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._create_tables()
        logger.info("Database initialized successfully")

    def _create_tables(self):
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','teacher','security')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, roll_no TEXT NOT NULL,
            class TEXT NOT NULL, section TEXT DEFAULT '',
            phone TEXT DEFAULT '', guardian TEXT DEFAULT '',
            photo_path TEXT DEFAULT '', face_embedding NPARRAY,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(roll_no, class)
        );
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL, date DATE NOT NULL,
            time TIME NOT NULL, status TEXT DEFAULT 'Present',
            confidence REAL DEFAULT 0.0,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            UNIQUE(student_id, date)
        );
        CREATE TABLE IF NOT EXISTS visitors (
            visitor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_time DATETIME NOT NULL, exit_time DATETIME,
            snapshot_path TEXT DEFAULT '', confidence REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Inside'
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
        CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
        CREATE INDEX IF NOT EXISTS idx_visitors_entry ON visitors(entry_time);
        CREATE INDEX IF NOT EXISTS idx_students_class ON students(class, section);
        """
        with self._db_lock:
            self._connection.executescript(schema)
            self._connection.commit()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._db_lock:
            cursor = self._connection.execute(query, params)
            self._connection.commit()
            return cursor

    def execute_many(self, query: str, params_list: list):
        with self._db_lock:
            self._connection.executemany(query, params_list)
            self._connection.commit()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        with self._db_lock:
            cursor = self._connection.execute(query, params)
            return cursor.fetchone()

    def fetch_all(self, query: str, params: tuple = ()) -> list:
        with self._db_lock:
            cursor = self._connection.execute(query, params)
            return cursor.fetchall()

    def backup(self) -> str:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = BACKUPS_DIR / f"visionai_backup_{ts}.db"
        with self._db_lock:
            backup_conn = sqlite3.connect(str(path))
            self._connection.backup(backup_conn)
            backup_conn.close()
        logger.info(f"Database backed up to: {path}")
        return str(path)

    def restore(self, backup_path: str) -> bool:
        bp = Path(backup_path)
        if not bp.exists():
            return False
        with self._db_lock:
            self._connection.close()
            shutil.copy2(str(bp), str(self._db_path))
            self._connection = sqlite3.connect(
                str(self._db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA foreign_keys=ON")
        logger.info(f"Database restored from: {backup_path}")
        return True

    def close(self):
        with self._db_lock:
            if self._connection:
                self._connection.close()
                logger.info("Database connection closed")

    def get_table_count(self, table: str) -> int:
        row = self.fetch_one(f"SELECT COUNT(*) as cnt FROM {table}")
        return row["cnt"] if row else 0

# Optimized connection lifecycle and WAL checkpointing
