"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(level: int = logging.INFO, log_file: Optional[Path] = None) -> None:
    """Configure application-wide logging.
    
    Args:
        level: Logging level (e.g., logging.INFO).
        log_file: Optional path to log file. If None, logs to console only.
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if path provided)
    if log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except OSError as e:
            root_logger.warning("Failed to create log file %s: %s", log_file, e)
    
    # Reduce noise from third-party libraries
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    
    root_logger.info("Logging initialized at level %s", logging.getLevelName(level))
