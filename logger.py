"""
logger.py — Shared logging setup used across all modules
"""

import logging
import os
from config import LOG_FILE

os.makedirs("logs", exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """Return a named logger writing to file + console."""
    logger = logging.getLogger(name)

    if logger.handlers:          # Avoid duplicate handlers on re-import
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    # File handler
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger
