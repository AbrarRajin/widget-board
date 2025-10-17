"""Main application entry point."""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.config import Config
from storage.repository import StorageRepository
from ui.main_window import MainWindow


def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting WidgetBoard application")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("WidgetBoard")
    app.setOrganizationName("WidgetBoard")
    
    # Set application style
    app.setStyle("Fusion")
    
    try:
        # Load configuration
        logger.info("Loading configuration")
        config = Config()  # Config is instantiated directly, not loaded
        
        # Initialize database
        logger.info("Initializing database")
        db_path = Path(config.data_dir) / "app.db"
        repository = StorageRepository(db_path)  # Pass Path object, not string
        repository.initialize()
        
        # Create main window
        logger.info("Creating main window")
        window = MainWindow(config, repository)
        
        # Fix window geometry to ensure it's visible and properly sized
        screen = app.primaryScreen().availableGeometry()
        
        # Calculate reasonable window size (80% of screen, max 1400x900)
        window_width = min(1400, int(screen.width() * 0.8))
        window_height = min(900, int(screen.height() * 0.8))
        
        # Ensure minimum size
        window_width = max(800, window_width)
        window_height = max(600, window_height)
        
        logger.info(f"Screen size: {screen.width()}x{screen.height()}")
        logger.info(f"Window size: {window_width}x{window_height}")
        
        # Set window size
        window.resize(window_width, window_height)
        
        # Center window on screen
        window_geometry = window.frameGeometry()
        window_geometry.moveCenter(screen.center())
        window.move(window_geometry.topLeft())
        
        # Ensure window is not maximized or fullscreen
        window.setWindowState(Qt.WindowState.WindowNoState)
        
        # Show window
        window.show()
        
        logger.info("Application ready")
        
        # Run event loop
        exit_code = app.exec()
        
        # Cleanup
        logger.info("Application shutting down")
        repository.close()
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()