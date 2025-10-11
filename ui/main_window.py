"""Main application window."""

import logging
import uuid
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel,
    QMenuBar, QMenu, QMessageBox, QInputDialog, QScrollArea, QFileDialog
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence

from core.config import Config
from core.models import Page, Tile
from core.grid_controller import GridController
from core.schema_loader import SchemaLoader
from storage.repository import StorageRepository
from storage.import_export import LayoutImportExport
from ui.theme_manager import ThemeManager
from ui.grid_view import GridView
from ui.page_manager import PageManager
from ui.settings_dialog import SettingsDialog
from ui.app_settings_dialog import AppSettingsDialog

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with menu bar and central widget."""
    
    def __init__(self, config: Config, repository: StorageRepository) -> None:
        """Initialize main window.
        
        Args:
            config: Application configuration.
            repository: Storage repository.
        """
        super().__init__()
        
        self.config = config
        self.repository = repository
        self.theme_manager = ThemeManager()
        self.grid_controller = GridController()
        self.import_export = LayoutImportExport(repository)
        self.schema_loader = SchemaLoader()
        
        # State
        self.is_edit_mode = False
        
        self._setup_ui()
        self._create_menus()
        self._apply_initial_theme()
        self._load_initial_data()
        
        logger.info("Main window initialized")
    
    def _setup_ui(self) -> None:
        """Set up the main window UI."""
        self.setWindowTitle("WidgetBoard")
        self.resize(self.config.window_width, self.config.window_height)
        
        # Create central widget
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Page manager at top
        self.page_manager = PageManager()
        self.page_manager.page_changed.connect(self._on_page_changed)
        self.page_manager.page_add_requested.connect(self._on_new_page)
        self.page_manager.page_remove_requested.connect(self._on_remove_page)
        layout.addWidget(self.page_manager)
        
        # Grid view in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(False)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.grid_view = GridView(self.grid_controller)
        self.grid_view.layout_changed.connect(self._on_layout_changed)
        scroll_area.setWidget(self.grid_view)
        
        layout.addWidget(scroll_area, 1)
        
        self.setCentralWidget(central_widget)
    
    def _create_menus(self) -> None:
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_page_action = QAction("&New Page", self)
        new_page_action.setShortcut(QKeySequence.StandardKey.New)
        new_page_action.triggered.connect(self._on_new_page)
        file_menu.addAction(new_page_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("&Import Layout...", self)
        import_action.triggered.connect(self._on_import_layout)
        file_menu.addAction(import_action)
        
        export_action = QAction("&Export Layout...", self)
        export_action.triggered.connect(self._on_export_layout)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        edit_mode_action = QAction("Toggle &Edit Mode", self)
        edit_mode_action.setShortcut(QKeySequence("Ctrl+E"))
        edit_mode_action.setCheckable(True)
        edit_mode_action.triggered.connect(self._on_toggle_edit_mode)
        edit_menu.addAction(edit_mode_action)
        self.edit_mode_action = edit_mode_action  # Store for later access
        
        edit_menu.addSeparator()
        
        # Add test tile action (for M1 testing)
        add_tile_action = QAction("Add Test &Tile", self)
        add_tile_action.setShortcut(QKeySequence("Ctrl+T"))
        add_tile_action.triggered.connect(self._on_add_test_tile)
        edit_menu.addAction(add_tile_action)
        
        edit_menu.addSeparator()
        
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut(QKeySequence.StandardKey.Preferences)
        settings_action.triggered.connect(self._on_settings)
        edit_menu.addAction(settings_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        theme_action = QAction("Toggle T&heme", self)
        theme_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        theme_action.triggered.connect(self._on_toggle_theme)
        view_menu.addAction(theme_action)
        
        view_menu.addSeparator()
        
        fullscreen_action = QAction("&Full Screen", self)
        fullscreen_action.setShortcut(QKeySequence.StandardKey.FullScreen)
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self._on_toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Plugins menu
        plugins_menu = menubar.addMenu("&Plugins")
        
        plugin_manager_action = QAction("&Manage Plugins...", self)
        plugin_manager_action.triggered.connect(self._on_plugin_manager)
        plugins_menu.addAction(plugin_manager_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _apply_initial_theme(self) -> None:
        """Apply the theme from configuration."""
        self.theme_manager.apply_theme(self.config.theme)
    
    def _load_initial_data(self) -> None:
        """Load pages and tiles from database."""
        pages_data = self.repository.get_all_pages()
        
        if not pages_data:
            # Create default page if none exist
            page_id = self.repository.create_page("Dashboard", index_order=0)
            pages_data = [{'id': page_id, 'name': 'Dashboard', 'index_order': 0}]
            logger.info("Created default page")
        
        # Convert to Page objects
        pages = [Page(**p) for p in pages_data]
        self.page_manager.set_pages(pages)
        
        # Load first page
        if pages:
            self._on_page_changed(pages[0])
    
    # Menu action handlers
    
    def _on_new_page(self) -> None:
        """Handle new page action."""
        name, ok = QInputDialog.getText(
            self,
            "New Page",
            "Enter page name:",
            text=f"Page {len(self.page_manager.pages) + 1}"
        )
        
        if ok and name:
            page_id = self.repository.create_page(name, len(self.page_manager.pages))
            new_page = Page(id=page_id, name=name, index_order=len(self.page_manager.pages))
            self.page_manager.add_page(new_page)
            logger.info("Created new page: %s", name)
    
    def _on_remove_page(self, page: Page) -> None:
        """Handle page removal.
        
        Args:
            page: Page that was removed.
        """
        self.repository.delete_page(page.id)
        logger.info("Deleted page: %s", page.name)
    
    def _on_page_changed(self, page: Page) -> None:
        """Handle page change.
        
        Args:
            page: New current page.
        """
        # Load tiles for this page
        tiles_data = self.repository.get_tiles_for_page(page.id)
        tiles = [Tile.from_dict(t) for t in tiles_data]
        
        # Update grid view
        self.grid_view.set_page(page, tiles)
        logger.info("Switched to page: %s", page.name)
    
    def _on_layout_changed(self) -> None:
        """Handle layout change - save to database."""
        if not self.page_manager.current_page:
            return
        
        tiles = self.grid_view.get_tiles()
        tiles_data = [t.to_dict() for t in tiles]
        
        self.repository.save_tiles_for_page(
            self.page_manager.current_page.id,
            tiles_data
        )
        logger.debug("Saved layout for page %s", self.page_manager.current_page.name)
    
    def _on_import_layout(self) -> None:
        """Handle import layout action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Layout",
            str(Path.home()),
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Ask merge or replace
        reply = QMessageBox.question(
            self,
            "Import Mode",
            "Merge with existing layout?\n\n"
            "Yes: Keep existing pages and add imported ones\n"
            "No: Replace all pages with imported layout",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Cancel:
            return
        
        merge = reply == QMessageBox.StandardButton.Yes
        
        try:
            # Validate first
            is_valid, error_msg = self.import_export.validate_layout(Path(file_path))
            if not is_valid:
                QMessageBox.critical(
                    self,
                    "Invalid Layout File",
                    f"Cannot import layout:\n\n{error_msg}"
                )
                return
            
            # Import
            pages_count, tiles_count = self.import_export.import_layout(
                Path(file_path),
                merge=merge
            )
            
            # Reload UI
            self._load_initial_data()
            
            QMessageBox.information(
                self,
                "Import Successful",
                f"Imported {pages_count} page(s) with {tiles_count} tile(s)."
            )
            
            logger.info("Imported layout from: %s", file_path)
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Failed to import layout:\n\n{str(e)}"
            )
            logger.error("Import failed: %s", e, exc_info=True)
    
    def _on_export_layout(self) -> None:
        """Handle export layout action."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Layout",
            str(Path.home() / "widgetboard_layout.json"),
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            self.import_export.export_layout(Path(file_path))
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Layout exported to:\n{file_path}"
            )
            
            logger.info("Exported layout to: %s", file_path)
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export layout:\n\n{str(e)}"
            )
            logger.error("Export failed: %s", e, exc_info=True)
    
    def _on_toggle_edit_mode(self, checked: bool) -> None:
        """Handle edit mode toggle.
        
        Args:
            checked: Whether edit mode is enabled.
        """
        self.is_edit_mode = checked
        self.grid_view.set_edit_mode(checked)
        logger.info("Edit mode: %s", "enabled" if checked else "disabled")
        
        # Show message on first enable
        if checked:
            QMessageBox.information(
                self,
                "Edit Mode",
                "Edit Mode Enabled!\n\n"
                "• Drag tiles to move them\n"
                "• Drag bottom-right corner to resize\n"
                "• Arrow keys to move selected tile\n"
                "• Shift+Arrow keys to resize\n"
                "• Delete key to remove tile\n"
                "• Right-click for more options (coming in M5)"
            )
    
    def _on_add_test_tile(self) -> None:
        """Add a test tile to the current page."""
        if not self.page_manager.current_page:
            QMessageBox.warning(self, "No Page", "Create a page first.")
            return
        
        # Find an empty slot
        slot = self.grid_controller.find_empty_slot(2, 2)
        
        if slot is None:
            QMessageBox.warning(
                self,
                "Grid Full",
                "No space available for a new tile."
            )
            return
        
        row, col = slot
        
        # Create test tile
        tile = Tile(
            id=None,
            page_id=self.page_manager.current_page.id,
            plugin_id="test_widget",
            instance_id=str(uuid.uuid4()),
            row=row,
            col=col,
            width=2,
            height=2,
            z_index=0
        )
        
        # Add to grid
        if self.grid_view.add_tile(tile):
            logger.info("Added test tile at (%d, %d)", row, col)
        else:
            QMessageBox.warning(
                self,
                "Cannot Add Tile",
                "Failed to add tile due to collision."
            )
    
    def _on_settings(self) -> None:
        """Handle settings action."""
        dialog = AppSettingsDialog(self.config, self)
        if dialog.exec():
            # Apply theme if changed
            self.theme_manager.apply_theme(self.config.theme)
            logger.info("Settings applied")
    
    def _on_toggle_theme(self) -> None:
        """Handle theme toggle action."""
        new_theme = self.theme_manager.toggle_theme()
        self.config.theme = new_theme
        self.config.save_settings()
        logger.info("Theme toggled to: %s", new_theme)
    
    def _on_toggle_fullscreen(self, checked: bool) -> None:
        """Handle fullscreen toggle.
        
        Args:
            checked: Whether fullscreen is enabled.
        """
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()
        logger.info("Fullscreen toggled: %s", checked)
    
    def _on_plugin_manager(self) -> None:
        """Handle plugin manager action."""
        logger.info("Plugin manager requested (stub)")
        QMessageBox.information(
            self,
            "Plugin Manager",
            "Plugin management will be implemented in M8."
        )
    
    def _on_about(self) -> None:
        """Handle about action."""
        QMessageBox.about(
            self,
            "About WidgetBoard",
            f"<h3>WidgetBoard {self.config.version}</h3>"
            "<p>A grid-based dashboard application with plugin support.</p>"
            "<p>Built with PySide6 and Python.</p>"
        )
    
    def closeEvent(self, event) -> None:
        """Handle window close event.
        
        Args:
            event: Close event.
        """
        # Save window geometry
        self.config.window_width = self.width()
        self.config.window_height = self.height()
        self.config.save_settings()
        
        # Close database
        self.repository.close()
        
        logger.info("Application closing")
        event.accept()