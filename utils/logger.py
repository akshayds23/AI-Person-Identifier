"""
VisionAI Campus - Logger Utility
=================================
Rotating file logger with console output.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from config import LOGS_DIR, APP_NAME


def setup_logger(name: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Create and configure a logger instance.
    
    Args:
        name: Logger name (defaults to APP_NAME)
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    logger_name = name or APP_NAME
    logger = logging.getLogger(logger_name)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # --- Format ---
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    # --- File Handler (rotating, 5 MB max, keep 3 backups) ---
    log_file = LOGS_DIR / "app.log"
    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


# Module-level default logger
logger = setup_logger()
