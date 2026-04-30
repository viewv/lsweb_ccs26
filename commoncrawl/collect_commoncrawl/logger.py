import logging
import os
import sys
import settings
from logging.handlers import RotatingFileHandler

def get_logger(name: str,
               log_file: str = "app.log",
               level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger with stdout + rotating file handler."""

    # ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = settings.ROOT_DIR
    log_dir = os.path.join(ROOT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, log_file)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # --- Rotating File Handler ---
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=5 * 1024 * 1024,   # 5 MB
            backupCount=5               # keep last 5 rotated files
        )
        file_handler.setLevel(level)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        # --- Stdout Handler ---
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(level)
        stream_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)

    return logger
