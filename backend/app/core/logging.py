"""Application logging setup.

Mirrors the format used by the ingestion pipeline
(``backend/ingestion/logger.py``) so logs are consistent across the service,
while keeping the API package self-contained (no cross-package import path
assumptions).
"""
import logging
import os
from logging.handlers import RotatingFileHandler


def get_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        try:
            log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
            os.makedirs(log_dir, exist_ok=True)
            file_handler = RotatingFileHandler(
                os.path.join(log_dir, "api.log"),
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # On read-only containers (like Catalyst AppSail), file logging will fail.
            # We fallback silently to console logging (stdout), which is automatically collected by Catalyst logs.
            logger.warning(f"Could not initialize file logging (filesystem may be read-only): {e}")

    return logger
