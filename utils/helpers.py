"""
VisionAI Campus - Utility Helpers
==================================
Common utility functions used across the application.
"""

import hashlib
import os
import shutil
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional


# ============================================
# Password Hashing
# ============================================

def generate_salt(length: int = 32) -> str:
    """Generate a random salt for password hashing."""
    return os.urandom(length).hex()


def hash_password(password: str, salt: str) -> str:
    """Hash a password with SHA-256 and a salt."""
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password, salt) == password_hash


# ============================================
# Time & Date Formatting
# ============================================

def format_time(dt: Optional[datetime] = None) -> str:
    """Format datetime to time string (HH:MM:SS)."""
    dt = dt or datetime.now()
    return dt.strftime("%H:%M:%S")


def format_date(dt: Optional[datetime] = None) -> str:
    """Format datetime to date string (YYYY-MM-DD)."""
    dt = dt or datetime.now()
    return dt.strftime("%Y-%m-%d")


def format_datetime(dt: Optional[datetime] = None) -> str:
    """Format datetime to full string (YYYY-MM-DD HH:MM:SS)."""
    dt = dt or datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_time_short(dt: Optional[datetime] = None) -> str:
    """Format datetime to short time (HH:MM)."""
    dt = dt or datetime.now()
    return dt.strftime("%H:%M")


# ============================================
# Storage Utilities
# ============================================

def get_storage_usage(path: Path) -> dict:
    """
    Get storage usage statistics for a directory.
    
    Returns:
        dict with 'total_mb', 'used_mb', 'free_mb', 'percent_used'
    """
    try:
        usage = shutil.disk_usage(str(path))
        return {
            "total_mb": round(usage.total / (1024 * 1024), 1),
            "used_mb": round(usage.used / (1024 * 1024), 1),
            "free_mb": round(usage.free / (1024 * 1024), 1),
            "percent_used": round((usage.used / usage.total) * 100, 1),
        }
    except Exception:
        return {"total_mb": 0, "used_mb": 0, "free_mb": 0, "percent_used": 0}


def get_folder_size_mb(path: Path) -> float:
    """Get total size of a folder in megabytes."""
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
    except Exception:
        pass
    return round(total / (1024 * 1024), 2)


# ============================================
# CSV Utilities
# ============================================

def validate_csv(file_path: str, required_columns: list) -> tuple:
    """
    Validate a CSV file has the required columns.
    
    Args:
        file_path: Path to CSV file
        required_columns: List of required column names
    
    Returns:
        (is_valid: bool, message: str, rows: list)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

            missing = [c for c in required_columns if c not in headers]
            if missing:
                return False, f"Missing columns: {', '.join(missing)}", []

            rows = list(reader)
            if not rows:
                return False, "CSV file is empty", []

            return True, f"Valid CSV with {len(rows)} rows", rows

    except FileNotFoundError:
        return False, "File not found", []
    except Exception as e:
        return False, f"Error reading CSV: {str(e)}", []


# ============================================
# Image Utilities
# ============================================

def sanitize_filename(name: str) -> str:
    """Sanitize a string to be safe for use as a filename."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for ch in invalid_chars:
        name = name.replace(ch, "_")
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Collapse multiple consecutive underscores
    import re
    name = re.sub(r'_+', '_', name)
    return name.strip("_").strip(".")


def generate_photo_filename(student_name: str, roll_no: str, index: int = 0) -> str:
    """Generate a standardized photo filename."""
    safe_name = sanitize_filename(student_name)
    safe_roll = sanitize_filename(roll_no)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_roll}_{safe_name}_{timestamp}_{index}.jpg"


def generate_snapshot_filename() -> str:
    """Generate a filename for a visitor snapshot."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"visitor_{timestamp}.jpg"
