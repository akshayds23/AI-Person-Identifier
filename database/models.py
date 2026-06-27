"""
VisionAI Campus - Data Models & CRUD Operations
=================================================
"""

import csv
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple

import numpy as np

from database.db import DatabaseManager
from utils.helpers import generate_salt, hash_password, verify_password
from utils.logger import logger
from config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD


def _get_db() -> DatabaseManager:
    return DatabaseManager.get_instance()


# ============================================
# User Model
# ============================================

class UserModel:
    @staticmethod
    def initialize_default_admin():
        db = _get_db()
        existing = db.fetch_one("SELECT user_id FROM users WHERE username=?",
                                (DEFAULT_ADMIN_USERNAME,))
        if not existing:
            salt = generate_salt()
            pw_hash = hash_password(DEFAULT_ADMIN_PASSWORD, salt)
            db.execute(
                "INSERT INTO users (username, password_hash, salt, role) VALUES (?,?,?,?)",
                (DEFAULT_ADMIN_USERNAME, pw_hash, salt, "admin"),
            )
            logger.info("Default admin account created")

    @staticmethod
    def authenticate(username: str, password: str) -> Optional[dict]:
        db = _get_db()
        row = db.fetch_one("SELECT * FROM users WHERE username=?", (username,))
        if row and verify_password(password, row["salt"], row["password_hash"]):
            return dict(row)
        return None

    @staticmethod
    def create_user(username: str, password: str, role: str) -> bool:
        db = _get_db()
        salt = generate_salt()
        pw_hash = hash_password(password, salt)
        try:
            db.execute(
                "INSERT INTO users (username, password_hash, salt, role) VALUES (?,?,?,?)",
                (username, pw_hash, salt, role),
            )
            return True
        except Exception as e:
            logger.error(f"Create user failed: {e}")
            return False

    @staticmethod
    def update_password(user_id: int, new_password: str) -> bool:
        db = _get_db()
        salt = generate_salt()
        pw_hash = hash_password(new_password, salt)
        db.execute("UPDATE users SET password_hash=?, salt=? WHERE user_id=?",
                    (pw_hash, salt, user_id))
        return True

    @staticmethod
    def get_all_users() -> list:
        db = _get_db()
        rows = db.fetch_all("SELECT user_id, username, role, created_at FROM users")
        return [dict(r) for r in rows]


# ============================================
# Student Model
# ============================================

class StudentModel:
    @staticmethod
    def add(name: str, roll_no: str, cls: str, section: str = "",
            phone: str = "", guardian: str = "", photo_path: str = "",
            face_embedding: np.ndarray = None) -> Optional[int]:
        db = _get_db()
        try:
            cursor = db.execute(
                """INSERT INTO students
                   (name, roll_no, class, section, phone, guardian, photo_path, face_embedding)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (name, roll_no, cls, section, phone, guardian, photo_path, face_embedding),
            )
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Add student failed: {e}")
            return None

    @staticmethod
    def update(student_id: int, **kwargs) -> bool:
        db = _get_db()
        allowed = {"name", "roll_no", "class", "section", "phone",
                    "guardian", "photo_path", "face_embedding"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        set_clause = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [student_id]
        db.execute(f"UPDATE students SET {set_clause} WHERE student_id=?", tuple(values))
        return True

    @staticmethod
    def delete(student_id: int) -> bool:
        db = _get_db()
        db.execute("DELETE FROM students WHERE student_id=?", (student_id,))
        return True

    @staticmethod
    def get(student_id: int) -> Optional[dict]:
        db = _get_db()
        row = db.fetch_one("SELECT * FROM students WHERE student_id=?", (student_id,))
        return dict(row) if row else None

    @staticmethod
    def get_all() -> list:
        db = _get_db()
        rows = db.fetch_all(
            "SELECT student_id, name, roll_no, class, section, phone, guardian, photo_path, created_at FROM students ORDER BY class, roll_no"
        )
        return [dict(r) for r in rows]

    @staticmethod
    def search(query: str) -> list:
        db = _get_db()
        q = f"%{query}%"
        rows = db.fetch_all(
            """SELECT student_id, name, roll_no, class, section, phone, guardian, photo_path
               FROM students WHERE name LIKE ? OR roll_no LIKE ? OR class LIKE ?
               ORDER BY class, roll_no""",
            (q, q, q),
        )
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_class(cls: str, section: str = "") -> list:
        db = _get_db()
        if section:
            rows = db.fetch_all(
                "SELECT * FROM students WHERE class=? AND section=? ORDER BY roll_no",
                (cls, section),
            )
        else:
            rows = db.fetch_all(
                "SELECT * FROM students WHERE class=? ORDER BY roll_no", (cls,),
            )
        return [dict(r) for r in rows]

    @staticmethod
    def get_classes() -> list:
        db = _get_db()
        rows = db.fetch_all("SELECT DISTINCT class FROM students ORDER BY class")
        return [r["class"] for r in rows]

    @staticmethod
    def get_all_embeddings() -> List[Tuple[int, str, np.ndarray]]:
        db = _get_db()
        rows = db.fetch_all(
            "SELECT student_id, name, face_embedding FROM students WHERE face_embedding IS NOT NULL"
        )
        result = []
        for r in rows:
            emb = r["face_embedding"]
            if emb is not None:
                result.append((r["student_id"], r["name"], emb))
        return result

    @staticmethod
    def import_csv(file_path: str) -> Tuple[int, int, list]:
        success, failed, errors = 0, 0, []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader, 1):
                    try:
                        StudentModel.add(
                            name=row.get("name", ""),
                            roll_no=row.get("roll_no", ""),
                            cls=row.get("class", ""),
                            section=row.get("section", ""),
                            phone=row.get("phone", ""),
                            guardian=row.get("guardian", ""),
                        )
                        success += 1
                    except Exception as e:
                        failed += 1
                        errors.append(f"Row {i}: {e}")
        except Exception as e:
            errors.append(str(e))
        return success, failed, errors

    @staticmethod
    def export_csv(file_path: str) -> bool:
        students = StudentModel.get_all()
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["name", "roll_no", "class", "section", "phone", "guardian"]
                )
                writer.writeheader()
                for s in students:
                    writer.writerow({k: s.get(k, "") for k in writer.fieldnames})
            return True
        except Exception as e:
            logger.error(f"Export CSV failed: {e}")
            return False

    @staticmethod
    def count() -> int:
        return _get_db().get_table_count("students")


# ============================================
# Attendance Model
# ============================================

class AttendanceModel:
    @staticmethod
    def mark(student_id: int, confidence: float = 0.0,
             status: str = "Present") -> bool:
        db = _get_db()
        today = date.today().isoformat()
        now = datetime.now().strftime("%H:%M:%S")
        try:
            db.execute(
                "INSERT OR IGNORE INTO attendance (student_id, date, time, status, confidence) VALUES (?,?,?,?,?)",
                (student_id, today, now, status, confidence),
            )
            return True
        except Exception as e:
            logger.error(f"Mark attendance failed: {e}")
            return False

    @staticmethod
    def is_marked_today(student_id: int) -> bool:
        db = _get_db()
        today = date.today().isoformat()
        row = db.fetch_one(
            "SELECT attendance_id FROM attendance WHERE student_id=? AND date=?",
            (student_id, today),
        )
        return row is not None

    @staticmethod
    def get_by_date(target_date: str, cls: str = "") -> list:
        db = _get_db()
        if cls:
            rows = db.fetch_all(
                """SELECT a.*, s.name, s.roll_no, s.class, s.section
                   FROM attendance a JOIN students s ON a.student_id=s.student_id
                   WHERE a.date=? AND s.class=? ORDER BY a.time""",
                (target_date, cls),
            )
        else:
            rows = db.fetch_all(
                """SELECT a.*, s.name, s.roll_no, s.class, s.section
                   FROM attendance a JOIN students s ON a.student_id=s.student_id
                   WHERE a.date=? ORDER BY a.time""",
                (target_date,),
            )
        return [dict(r) for r in rows]

    @staticmethod
    def get_report(start_date: str, end_date: str, cls: str = "") -> list:
        db = _get_db()
        if cls:
            rows = db.fetch_all(
                """SELECT a.*, s.name, s.roll_no, s.class, s.section
                   FROM attendance a JOIN students s ON a.student_id=s.student_id
                   WHERE a.date BETWEEN ? AND ? AND s.class=?
                   ORDER BY a.date, a.time""",
                (start_date, end_date, cls),
            )
        else:
            rows = db.fetch_all(
                """SELECT a.*, s.name, s.roll_no, s.class, s.section
                   FROM attendance a JOIN students s ON a.student_id=s.student_id
                   WHERE a.date BETWEEN ? AND ?
                   ORDER BY a.date, a.time""",
                (start_date, end_date),
            )
        return [dict(r) for r in rows]

    @staticmethod
    def get_today_count(cls: str = "") -> int:
        db = _get_db()
        today = date.today().isoformat()
        if cls:
            row = db.fetch_one(
                """SELECT COUNT(*) as cnt FROM attendance a
                   JOIN students s ON a.student_id=s.student_id
                   WHERE a.date=? AND s.class=?""",
                (today, cls),
            )
        else:
            row = db.fetch_one(
                "SELECT COUNT(*) as cnt FROM attendance WHERE date=?", (today,),
            )
        return row["cnt"] if row else 0

    @staticmethod
    def count() -> int:
        return _get_db().get_table_count("attendance")


# ============================================
# Visitor Model
# ============================================

class VisitorModel:
    @staticmethod
    def log_entry(confidence: float = 0.0, snapshot_path: str = "") -> int:
        db = _get_db()
        now = datetime.now().isoformat()
        cursor = db.execute(
            "INSERT INTO visitors (entry_time, snapshot_path, confidence, status) VALUES (?,?,?,?)",
            (now, snapshot_path, confidence, "Inside"),
        )
        return cursor.lastrowid

    @staticmethod
    def log_exit(visitor_id: int):
        db = _get_db()
        now = datetime.now().isoformat()
        db.execute(
            "UPDATE visitors SET exit_time=?, status='Left' WHERE visitor_id=?",
            (now, visitor_id),
        )

    @staticmethod
    def get_today() -> list:
        db = _get_db()
        today = date.today().isoformat()
        rows = db.fetch_all(
            "SELECT * FROM visitors WHERE DATE(entry_time)=? ORDER BY entry_time DESC",
            (today,),
        )
        return [dict(r) for r in rows]

    @staticmethod
    def get_today_count() -> dict:
        db = _get_db()
        today = date.today().isoformat()
        total = db.fetch_one(
            "SELECT COUNT(*) as cnt FROM visitors WHERE DATE(entry_time)=?", (today,),
        )
        inside = db.fetch_one(
            "SELECT COUNT(*) as cnt FROM visitors WHERE DATE(entry_time)=? AND status='Inside'",
            (today,),
        )
        return {
            "total": total["cnt"] if total else 0,
            "inside": inside["cnt"] if inside else 0,
        }

    @staticmethod
    def get_by_date_range(start_date: str, end_date: str) -> list:
        db = _get_db()
        rows = db.fetch_all(
            "SELECT * FROM visitors WHERE DATE(entry_time) BETWEEN ? AND ? ORDER BY entry_time DESC",
            (start_date, end_date),
        )
        return [dict(r) for r in rows]

    @staticmethod
    def count() -> int:
        return _get_db().get_table_count("visitors")


# ============================================
# Settings Model
# ============================================

class SettingsModel:
    @staticmethod
    def get(key: str, default: str = "") -> str:
        db = _get_db()
        row = db.fetch_one("SELECT value FROM settings WHERE key=?", (key,))
        return row["value"] if row else default

    @staticmethod
    def set(key: str, value: str):
        db = _get_db()
        db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)",
            (key, value),
        )

    @staticmethod
    def get_all() -> dict:
        db = _get_db()
        rows = db.fetch_all("SELECT key, value FROM settings")
        return {r["key"]: r["value"] for r in rows}

    @staticmethod
    def set_many(data: dict):
        db = _get_db()
        db.execute_many(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)",
            list(data.items()),
        )

    @staticmethod
    def is_setup_complete() -> bool:
        return SettingsModel.get("setup_complete") == "true"

    @staticmethod
    def mark_setup_complete():
        SettingsModel.set("setup_complete", "true")
