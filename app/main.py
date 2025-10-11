"""Application entry point."""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.logging_setup import setup_logging
from core.config import Config
from storage.repository import StorageRepository
from ui.main_window import MainWindow


def main() -> int:
    """Initialize and run the application.
    
    Returns:
        Exit code (0 for success).
    """
    # Enable High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Initialize logging
    config = Config()
    setup_logging(config.log_level, config.log_file)
    logger = logging.getLogger(__name__)
    logger.info("Starting WidgetBoard v%s", config.version)
    
    # Initialize storage
    try:
        repository = StorageRepository(config.database_path)
        repository.initialize()
        logger.info("Storage initialized at %s", config.database_path)
    except Exception as e:
        logger.error("Failed to initialize storage: %s", e)
        return 1
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("WidgetBoard")
    app.setOrganizationName("WidgetBoard")
    app.setApplicationVersion(config.version)
    
    # Create and show main window
    window = MainWindow(config, repository)
    window.show()
    
    logger.info("Application ready")
    
    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
