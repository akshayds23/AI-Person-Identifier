"""
VisionAI Campus - Configuration Module
=======================================
Loads all configuration from environment variables (.env file).
No values are hardcoded — everything is configurable via .env
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# --- Determine base directory ---
# When frozen (PyInstaller), use the executable's directory
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

# --- Load .env file ---
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)


def env(key: str, default: str = "") -> str:
    """Get an environment variable with a fallback default."""
    return os.getenv(key, default)


def env_int(key: str, default: int = 0) -> int:
    """Get an environment variable as integer."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def env_float(key: str, default: float = 0.0) -> float:
    """Get an environment variable as float."""
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def env_bool(key: str, default: bool = False) -> bool:
    """Get an environment variable as boolean."""
    val = os.getenv(key, str(default)).lower()
    return val in ("true", "1", "yes", "on")


def env_path(key: str, default: str = "") -> Path:
    """Get an environment variable as a resolved Path relative to BASE_DIR."""
    raw = os.getenv(key, default)
    if not raw:
        return Path("")
    p = Path(raw)
    if not p.is_absolute():
        p = BASE_DIR / p
    return p


# ============================================
# Application Settings
# ============================================
APP_NAME = env("APP_NAME", "VisionAI Campus")
APP_VERSION = env("APP_VERSION", "1.0.0")
APP_LANGUAGE = env("APP_LANGUAGE", "en")

# ============================================
# School Info
# ============================================
SCHOOL_NAME = env("SCHOOL_NAME", "My School")
SCHOOL_LOGO_PATH = env_path("SCHOOL_LOGO_PATH")

# ============================================
# Default Admin (used only on first-run DB init)
# ============================================
DEFAULT_ADMIN_USERNAME = env("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = env("DEFAULT_ADMIN_PASSWORD", "admin123")

# ============================================
# Camera
# ============================================
CAMERA_INDEX = env_int("CAMERA_INDEX", 0)
CAMERA_WIDTH = env_int("CAMERA_RESOLUTION_WIDTH", 640)
CAMERA_HEIGHT = env_int("CAMERA_RESOLUTION_HEIGHT", 480)
CAMERA_FPS = env_int("CAMERA_FPS", 30)

# ============================================
# AI Models
# ============================================
YOLO_MODEL_PATH = env_path("YOLO_MODEL_PATH", "models/yolo11n.pt")
INSIGHTFACE_MODEL_NAME = env("INSIGHTFACE_MODEL_NAME", "buffalo_l")
INSIGHTFACE_MODEL_DIR = env_path("INSIGHTFACE_MODEL_DIR", "models/insightface")

# ============================================
# AI Thresholds
# ============================================
DETECTION_CONFIDENCE = env_float("DETECTION_CONFIDENCE", 0.5)
RECOGNITION_THRESHOLD = env_float("RECOGNITION_THRESHOLD", 0.6)
RECOGNITION_COOLDOWN = env_int("RECOGNITION_COOLDOWN_SECONDS", 30)

# ============================================
# Storage Paths
# ============================================
DATABASE_PATH = env_path("DATABASE_PATH", "data/visionai.db")
PHOTOS_DIR = env_path("PHOTOS_DIR", "assets/photos")
SNAPSHOTS_DIR = env_path("SNAPSHOTS_DIR", "assets/snapshots")
BACKUPS_DIR = env_path("BACKUPS_DIR", "backups")
LOGS_DIR = env_path("LOGS_DIR", "logs")

# ============================================
# Theme
# ============================================
THEME = env("THEME", "dark")

# ============================================
# Performance Tuning
# ============================================
AI_PROCESS_EVERY_N_FRAMES = env_int("AI_PROCESS_EVERY_N_FRAMES", 3)
AUTO_SAVE_INTERVAL = env_int("AUTO_SAVE_INTERVAL_SECONDS", 60)
MAX_DISAPPEARED_FRAMES = env_int("MAX_DISAPPEARED_FRAMES", 50)
TRACKER_LINE_POSITION = env_float("TRACKER_LINE_POSITION", 0.5)

# ============================================
# Derived Paths & Directories
# ============================================
STYLES_DIR = BASE_DIR / "assets" / "styles"
ICONS_DIR = BASE_DIR / "assets" / "icons"
LOGOS_DIR = BASE_DIR / "assets" / "logos"
MODELS_DIR = BASE_DIR / "models"

# ============================================
# Ensure all required directories exist
# ============================================
REQUIRED_DIRS = [
    DATABASE_PATH.parent,
    PHOTOS_DIR,
    SNAPSHOTS_DIR,
    BACKUPS_DIR,
    LOGS_DIR,
    STYLES_DIR,
    ICONS_DIR,
    LOGOS_DIR,
    MODELS_DIR,
    INSIGHTFACE_MODEL_DIR,
]


def ensure_directories():
    """Create all required directories if they don't exist."""
    for d in REQUIRED_DIRS:
        if d and str(d):
            d.mkdir(parents=True, exist_ok=True)


# Run on import
ensure_directories()
