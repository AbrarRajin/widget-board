"""Main application window."""

import logging
import uuid
import json
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
from core.plugin_loader import PluginLoader
from storage.repository import StorageRepository
from storage.import_export import LayoutImportExport
from ui.theme_manager import ThemeManager
from ui.grid_view import GridView
from ui.page_manager import PageManager
from ui.settings_dialog import SettingsDialog
from ui.app_settings_dialog import AppSettingsDialog

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with menu bar and grid view."""
    
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
        self.plugin_loader = PluginLoader()
        
        # State
        self.is_edit_mode = False
        self.grid_view = None
        self.page_manager = None
        
        # Discover plugins
        self.plugin_loader.discover_plugins()
        logger.info(f"Discovered {len(self.plugin_loader.get_all_metadata())} plugins")
        
        # Setup UI
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
        
        self.grid_view = GridView(self.grid_controller, self)
        self.grid_view.layout_changed.connect(self._on_layout_changed)
        scroll_area.setWidget(self.grid_view)
        
        layout.addWidget(scroll_area, 1)
        
        self.setCentralWidget(central_widget)
    
    def _create_menus(self) -> None:
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        import_action = file_menu.addAction("Import Layout...")
        import_action.setShortcut(QKeySequence("Ctrl+O"))
        import_action.triggered.connect(self._on_import_layout)
        
        export_action = file_menu.addAction("Export Layout...")
        export_action.setShortcut(QKeySequence("Ctrl+S"))
        export_action.triggered.connect(self._on_export_layout)
        
        file_menu.addSeparator()
        
        settings_action = file_menu.addAction("Settings...")
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._on_settings)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        self.edit_mode_action = edit_menu.addAction("Toggle Edit Mode")
        self.edit_mode_action.setShortcut(QKeySequence("Ctrl+E"))
        self.edit_mode_action.setCheckable(True)
        self.edit_mode_action.triggered.connect(self._on_toggle_edit_mode)
        
        edit_menu.addSeparator()
        
        # Add test tile action
        add_test_action = edit_menu.addAction("Add Test Tile")
        add_test_action.setShortcut(QKeySequence("Ctrl+T"))
        add_test_action.triggered.connect(self._on_add_test_tile)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        fullscreen_action = view_menu.addAction("Full Screen")
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self._on_toggle_fullscreen)
        
        view_menu.addSeparator()
        
        theme_action = view_menu.addAction("Toggle Theme")
        theme_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        theme_action.triggered.connect(self._on_toggle_theme)
        
        # Plugins menu
        self._create_plugin_menu()
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._on_about)
    
    def _create_plugin_menu(self) -> None:
        """Create the Plugins menu with discovered plugins."""
        # Remove old plugin menu if exists
        menubar = self.menuBar()
        for action in menubar.actions():
            if action.text() == "&Plugins":
                menubar.removeAction(action)
                break
        
        plugin_menu = menubar.addMenu("&Plugins")
        
        # Get all discovered plugins
        plugins = self.plugin_loader.get_all_metadata()
        
        if not plugins:
            no_plugins_action = plugin_menu.addAction("No plugins found")
            no_plugins_action.setEnabled(False)
            return
        
        # Add action for each plugin
        for metadata in plugins:
            action = plugin_menu.addAction(f"Add {metadata.name}")
            action.setToolTip(metadata.description)
            # Connect to add_plugin_tile with the plugin_id
            action.triggered.connect(
                lambda checked=False, pid=metadata.plugin_id: self._add_plugin_tile(pid)
            )
        
        plugin_menu.addSeparator()
        
        # Reload plugins action
        reload_action = plugin_menu.addAction("Reload Plugins")
        reload_action.setShortcut("Ctrl+R")
        reload_action.triggered.connect(self._reload_plugins)
    
    def _apply_initial_theme(self) -> None:
        """Apply the initial theme from config."""
        self.theme_manager.apply_theme(self.config.theme)
    
    def _load_initial_data(self) -> None:
        """Load initial pages and tiles from database."""
        # Load pages
        pages_data = self.repository.get_all_pages()
        
        # Convert dict results to Page objects if needed
        pages = []
        for page_data in pages_data:
            if isinstance(page_data, dict):
                # Convert dict to Page object
                page = Page(
                    id=page_data['id'],
                    name=page_data['name'],
                    index_order=page_data['index_order']
                )
            else:
                # Already a Page object
                page = page_data
            pages.append(page)
        
        if not pages:
            # Create default page
            page_id = self.repository.create_page("Dashboard", 0)
            default_page = Page(id=page_id, name="Dashboard", index_order=0)
            pages = [default_page]
            logger.info("Created default page")
        
        # Set pages in grid controller
        self.grid_controller.pages = pages
        
        # Load tiles for all pages
        for page in pages:
            tiles_data = self.repository.get_tiles_for_page(page.id)
            
            # Convert dict results to Tile objects if needed
            tiles = []
            for tile_data in tiles_data:
                if isinstance(tile_data, dict):
                    # Handle state field - might be JSON string
                    state = tile_data.get('state', {})
                    if isinstance(state, str):
                        try:
                            state = json.loads(state)
                        except json.JSONDecodeError:
                            state = {}
                    elif state is None:
                        state = {}
                    
                    # Convert dict to Tile object
                    tile = Tile(
                        id=tile_data['id'],
                        page_id=tile_data['page_id'],
                        plugin_id=tile_data['plugin_id'],
                        instance_id=tile_data['instance_id'],
                        row=tile_data['row'],
                        col=tile_data['col'],
                        width=tile_data['width'],
                        height=tile_data['height'],
                        z_index=tile_data.get('z_index', 0),
                        state=state
                    )
                else:
                    # Already a Tile object
                    tile = tile_data
                tiles.append(tile)
            
            self.grid_controller.tiles_by_page[page.id] = tiles
            
            # Create plugin instances for tiles
            for tile in tiles:
                self._ensure_plugin_instance(tile)
            
            logger.info(f"Loaded {len(tiles)} tiles for page '{page.name}'")
        
        # Switch to first page
        if pages:
            self.grid_controller.switch_to_page(pages[0].id)
            # Set pages in page manager - this will automatically trigger page_changed signal
            self.page_manager.set_pages(pages)
            self.grid_view.refresh()
    
    def _ensure_plugin_instance(self, tile: Tile) -> None:
        """Ensure a plugin instance exists for a tile.
        
        Args:
            tile: The tile to create a plugin instance for.
        """
        # Check if instance already exists
        if self.plugin_loader.get_instance(tile.instance_id):
            return
        
        # Check if plugin exists
        metadata = self.plugin_loader.get_metadata(tile.plugin_id)
        if not metadata:
            logger.warning(f"Plugin not found for tile: {tile.plugin_id} (tile will be displayed without plugin)")
            return
        
        # Create plugin instance
        plugin = self.plugin_loader.create_instance(
            tile.plugin_id,
            tile.instance_id,
            tile.state
        )
        
        if plugin:
            # Start the plugin
            self.plugin_loader.start_instance(tile.instance_id)
            logger.debug(f"Created plugin instance: {tile.instance_id}")
        else:
            logger.warning(f"Failed to create plugin instance for {tile.plugin_id}")
    
    def _on_toggle_edit_mode(self, checked: bool) -> None:
        """Handle edit mode toggle.
        
        Args:
            checked: True if edit mode is now enabled.
        """
        self.is_edit_mode = checked
        
        if self.grid_view:
            self.grid_view.set_edit_mode(checked)
        
        if checked:
            QMessageBox.information(
                self,
                "Edit Mode",
                "Edit Mode Enabled\n\n"
                "• Drag tiles to move them\n"
                "• Drag bottom-right corner to resize\n"
                "• Press Delete to remove tiles\n"
                "• Use arrow keys to move selected tile\n"
                "• Use Shift+arrows to resize selected tile\n"
                "• Right-click for tile options"
            )
        
        logger.info(f"Edit mode: {checked}")
    
    def _on_add_test_tile(self) -> None:
        """Add a test tile to the current page."""
        if not self.grid_controller.current_page:
            QMessageBox.warning(self, "Error", "No active page")
            return
        
        # Find empty space
        position = self.grid_controller.find_empty_space(2, 2)
        
        if not position:
            QMessageBox.warning(
                self,
                "Grid Full",
                "No space available for new tile. Remove some tiles or create a new page."
            )
            return
        
        row, col = position
        
        # Create test tile
        tile = Tile(
            id=None,
            page_id=self.grid_controller.current_page.id,
            plugin_id="test_widget",
            instance_id=f"test_{uuid.uuid4().hex[:8]}",
            row=row,
            col=col,
            width=2,
            height=2,
            z_index=0,
            state={}
        )
        
        # Add to grid
        if self.grid_controller.add_tile(tile):
            self.grid_view.refresh()
            logger.info(f"Added test tile at ({row}, {col})")
    
    def _add_plugin_tile(self, plugin_id: str) -> None:
        """Add a tile with a specific plugin.
        
        Args:
            plugin_id: ID of the plugin to add.
        """
        if not self.grid_view:
            return
        
        metadata = self.plugin_loader.get_metadata(plugin_id)
        if not metadata:
            QMessageBox.warning(self, "Error", f"Plugin not found: {plugin_id}")
            return
        
        # Get current page
        current_page = self.grid_controller.current_page
        if not current_page:
            QMessageBox.warning(self, "Error", "No active page")
            return
        
        # Find empty space in grid
        position = self.grid_controller.find_empty_space(
            metadata.default_width,
            metadata.default_height
        )
        
        if not position:
            QMessageBox.warning(
                self,
                "Grid Full",
                "No space available for new tile. Remove some tiles or create a new page."
            )
            return
        
        row, col = position
        
        # Generate instance ID
        instance_id = f"{plugin_id}_{uuid.uuid4().hex[:8]}"
        
        # Get default settings from schema
        settings = {}
        if metadata.schema_path:
            try:
                import json
                with open(metadata.schema_path, 'r') as f:
                    schema = json.load(f)
                    # Extract default values from schema
                    for prop_name, prop_schema in schema.get("properties", {}).items():
                        if "default" in prop_schema:
                            settings[prop_name] = prop_schema["default"]
            except Exception as e:
                logger.error(f"Error loading schema defaults: {e}")
        
        # Create tile
        tile = Tile(
            id=None,
            page_id=current_page.id,
            plugin_id=plugin_id,
            instance_id=instance_id,
            row=row,
            col=col,
            width=metadata.default_width,
            height=metadata.default_height,
            z_index=0,
            state=settings
        )
        
        # Add to grid
        if self.grid_controller.add_tile(tile):
            # Create plugin instance
            plugin = self.plugin_loader.create_instance(
                plugin_id,
                instance_id,
                settings
            )
            
            if plugin:
                # Start the plugin
                self.plugin_loader.start_instance(instance_id)
                
                # Update grid view to show new tile with plugin
                self.grid_view.refresh()
                
                logger.info(f"Added {metadata.name} tile at ({row}, {col})")
            else:
                # Failed to create plugin, remove tile
                self.grid_controller.remove_tile(tile.id)
                QMessageBox.warning(
                    self,
                    "Plugin Error",
                    f"Failed to create plugin instance: {plugin_id}"
                )
    
    def _reload_plugins(self) -> None:
        """Reload all plugins from disk."""
        plugins = self.plugin_loader.discover_plugins()
        QMessageBox.information(
            self,
            "Plugins Reloaded",
            f"Discovered {len(plugins)} plugins"
        )
        
        # Rebuild plugin menu
        self._create_plugin_menu()
        
        logger.info(f"Reloaded plugins: {len(plugins)} found")
    
    def _on_toggle_fullscreen(self, checked: bool) -> None:
        """Handle fullscreen toggle.
        
        Args:
            checked: True if fullscreen should be enabled.
        """
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()
    
    def _on_toggle_theme(self) -> None:
        """Handle theme toggle."""
        new_theme = "dark" if self.config.theme == "light" else "light"
        self.config.theme = new_theme
        self.config.save_settings()
        self.theme_manager.apply_theme(new_theme)
        logger.info(f"Theme changed to: {new_theme}")
    
    def _on_page_changed(self, page: Page) -> None:
        """Handle page change.
        
        Args:
            page: The new current page.
        """
        # Stop plugins on old page
        if self.grid_controller.current_page:
            old_tiles = self.grid_controller.tiles_by_page.get(
                self.grid_controller.current_page.id, []
            )
            for tile in old_tiles:
                self.plugin_loader.stop_instance(tile.instance_id)
        
        # Switch to new page
        self.grid_controller.switch_to_page(page.id)
        
        # Start plugins on new page
        new_tiles = self.grid_controller.tiles_by_page.get(page.id, [])
        for tile in new_tiles:
            self.plugin_loader.start_instance(tile.instance_id)
        
        # Refresh view
        self.grid_view.refresh()
        logger.info(f"Switched to page: {page.name}")
    
    def _on_new_page(self) -> None:
        """Handle new page request."""
        name, ok = QInputDialog.getText(
            self,
            "New Page",
            "Enter page name:",
            text=f"Page {len(self.grid_controller.pages) + 1}"
        )
        
        if ok and name:
            # Insert into database
            page_id = self.repository.create_page(name, len(self.grid_controller.pages))
            
            # Create Page object
            new_page = Page(
                id=page_id,
                name=name,
                index_order=len(self.grid_controller.pages)
            )
            
            # Add to grid controller
            self.grid_controller.pages.append(new_page)
            self.grid_controller.tiles_by_page[page_id] = []
            
            # Synchronize with page manager - use set_pages to avoid duplicates
            self.page_manager.set_pages(self.grid_controller.pages)
            
            # Switch to the new page (it's the last one)
            self.page_manager.current_index = len(self.page_manager.pages) - 1
            self.page_manager.current_page = new_page
            self.page_manager.page_changed.emit(new_page)
            self.page_manager._update_buttons()
            
            logger.info(f"Created new page: {name}")
    
    def _on_remove_page(self, page: Page) -> None:
        """Handle page removal request.
        
        Args:
            page: The page that was removed (already removed from PageManager's list).
        """
        # PageManager has already removed the page from its list before emitting this signal
        # We just need to clean up the backend
        
        # Stop and dispose plugins on this page
        tiles = self.grid_controller.tiles_by_page.get(page.id, [])
        for tile in tiles:
            self.plugin_loader.destroy_instance(tile.instance_id)
        
        # Delete from database (this also deletes associated tiles via CASCADE)
        try:
            self.repository.delete_page(page.id)
        except Exception as e:
            logger.error(f"Failed to delete page from database: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete page: {e}")
            return
        
        # Remove from grid controller
        if page in self.grid_controller.pages:
            self.grid_controller.pages.remove(page)
        if page.id in self.grid_controller.tiles_by_page:
            del self.grid_controller.tiles_by_page[page.id]
        
        logger.info(f"Removed page: {page.name}")
    
    def _on_layout_changed(self) -> None:
        """Handle layout change event."""
        # Save current layout to database
        current_page = self.grid_controller.current_page
        if current_page:
            tiles = self.grid_controller.tiles_by_page.get(current_page.id, [])
            for tile in tiles:
                try:
                    if tile.id is None:
                        # New tile, insert it
                        tile_data = {
                            'page_id': tile.page_id,
                            'plugin_id': tile.plugin_id,
                            'instance_id': tile.instance_id,
                            'row': tile.row,
                            'col': tile.col,
                            'width': tile.width,
                            'height': tile.height,
                            'z_index': tile.z_index,
                            'state_json': json.dumps(tile.state)
                        }
                        tile.id = self.repository.create_tile(tile_data)
                    else:
                        # Existing tile, update it
                        tile_data = {
                            'row': tile.row,
                            'col': tile.col,
                            'width': tile.width,
                            'height': tile.height,
                            'z_index': tile.z_index,
                            'state_json': json.dumps(tile.state)
                        }
                        self.repository.update_tile(tile.id, tile_data)
                except Exception as e:
                    logger.error(f"Failed to save tile {tile.id}: {e}")
            
            # APSW uses autocommit - changes are automatically saved
            logger.debug("Layout saved to database")
    
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
        
        try:
            # Ask for import mode
            reply = QMessageBox.question(
                self,
                "Import Mode",
                "Replace all existing data?\n\n"
                "Yes: Replace everything\n"
                "No: Merge with existing data",
                QMessageBox.StandardButton.Yes | 
                QMessageBox.StandardButton.No | 
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            
            replace_all = (reply == QMessageBox.StandardButton.Yes)
            
            # Import layout
            pages, tiles = self.import_export.import_layout(
                Path(file_path),
                replace_all=replace_all
            )
            
            # Reload data
            self._load_initial_data()
            
            QMessageBox.information(
                self,
                "Import Successful",
                f"Imported {len(pages)} pages and {len(tiles)} tiles from:\n{file_path}"
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
    
    def _on_settings(self) -> None:
        """Handle settings action."""
        dialog = AppSettingsDialog(self.config, self)
        if dialog.exec():
            # Apply theme if changed
            self.theme_manager.apply_theme(self.config.theme)
            logger.info("Settings applied")
    
    def _on_about(self) -> None:
        """Handle about action."""
        QMessageBox.about(
            self,
            "About WidgetBoard",
            "<h3>WidgetBoard</h3>"
            "<p>A grid-based dashboard application with plugin support.</p>"
            "<p><b>Version:</b> M3 - Plugin Runtime</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>8×8 grid layout system</li>"
            "<li>Drag and drop tiles</li>"
            "<li>Multiple pages</li>"
            "<li>Plugin system</li>"
            "<li>Import/Export layouts</li>"
            "<li>Customizable settings</li>"
            "</ul>"
        )
    
    def closeEvent(self, event) -> None:
        """Handle window close event.
        
        Args:
            event: Close event.
        """
        # Save window size
        self.config.window_width = self.width()
        self.config.window_height = self.height()
        self.config.save_settings()
        
        # Stop all plugin instances
        for instance_id in list(self.plugin_loader._instances.keys()):
            self.plugin_loader.destroy_instance(instance_id)
        
        logger.info("Window closed, configuration saved")
        event.accept()