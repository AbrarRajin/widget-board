"""Main grid view for displaying and editing tiles."""

import logging
from typing import Dict, Optional
from pathlib import Path
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QPen

from core.models import Tile, Page
from core.grid_controller import GridController
from core.schema_loader import SchemaLoader
from ui.tile_widget import TileWidget
from ui.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class GridView(QWidget):
    """Main 8×8 grid view for tiles."""
    
    # Signals
    layout_changed = Signal()
    
    # Grid constants
    GRID_ROWS = 8
    GRID_COLS = 8
    MIN_CELL_SIZE = 80
    PREFERRED_CELL_SIZE = 120
    
    def __init__(self, controller: GridController, parent=None) -> None:
        """Initialize grid view.
        
        Args:
            controller: Grid controller for layout management.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.controller = controller
        self.current_page: Optional[Page] = None
        self.tile_widgets: Dict[str, TileWidget] = {}  # instance_id -> widget
        self.is_edit_mode = False
        self.cell_size = self.PREFERRED_CELL_SIZE
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the grid view UI."""
        self.setMinimumSize(
            self.MIN_CELL_SIZE * self.GRID_COLS,
            self.MIN_CELL_SIZE * self.GRID_ROWS
        )
        
        # Set background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#FFFFFF"))
        self.setPalette(palette)
    
    def sizeHint(self) -> QSize:
        """Provide size hint for layout.
        
        Returns:
            Preferred size for the grid.
        """
        return QSize(
            self.cell_size * self.GRID_COLS,
            self.cell_size * self.GRID_ROWS
        )
    
    def set_page(self, page: Page, tiles: list[Tile]) -> None:
        """Set the current page and its tiles.
        
        Args:
            page: Page to display.
            tiles: List of tiles on the page.
        """
        self.current_page = page
        
        # Clear existing widgets
        for widget in self.tile_widgets.values():
            widget.deleteLater()
        self.tile_widgets.clear()
        
        # Update controller
        self.controller.set_tiles(tiles)
        
        # Create widgets for tiles
        for tile in tiles:
            self._create_tile_widget(tile)
        
        logger.info("Loaded page '%s' with %d tiles", page.name, len(tiles))
        self.update()
    
    def _create_tile_widget(self, tile: Tile) -> TileWidget:
        """Create a widget for a tile.
        
        Args:
            tile: Tile to create widget for.
        
        Returns:
            Created tile widget.
        """
        widget = TileWidget(tile, self.cell_size, self)
        widget.set_edit_mode(self.is_edit_mode)
        widget.show()
        
        # Connect signals
        widget.move_requested.connect(lambda r, c, t=tile: self._on_tile_move(t, r, c))
        widget.resize_requested.connect(lambda w, h, t=tile: self._on_tile_resize(t, w, h))
        widget.remove_requested.connect(lambda t=tile: self._on_tile_remove(t))
        widget.settings_requested.connect(lambda t=tile: self._on_tile_settings(t))
        
        self.tile_widgets[tile.instance_id] = widget
        return widget
    
    def add_tile(self, tile: Tile) -> bool:
        """Add a new tile to the grid.
        
        Args:
            tile: Tile to add.
        
        Returns:
            True if tile was added successfully.
        """
        if self.controller.add_tile(tile):
            self._create_tile_widget(tile)
            self.layout_changed.emit()
            return True
        return False
    
    def set_edit_mode(self, enabled: bool) -> None:
        """Enable or disable edit mode.
        
        Args:
            enabled: True to enable edit mode.
        """
        self.is_edit_mode = enabled
        
        # Update all tile widgets
        for widget in self.tile_widgets.values():
            widget.set_edit_mode(enabled)
        
        logger.info("Edit mode: %s", "enabled" if enabled else "disabled")
        self.update()
    
    def _on_tile_move(self, tile: Tile, new_row: int, new_col: int) -> None:
        """Handle tile move request.
        
        Args:
            tile: Tile being moved.
            new_row: Target row.
            new_col: Target column.
        """
        if self.controller.move_tile(tile, new_row, new_col):
            # Update widget geometry
            widget = self.tile_widgets.get(tile.instance_id)
            if widget:
                widget.update_geometry()
            
            self.layout_changed.emit()
            logger.info("Moved tile %s to (%d, %d)", tile.instance_id, new_row, new_col)
    
    def _on_tile_resize(self, tile: Tile, new_width: int, new_height: int) -> None:
        """Handle tile resize request.
        
        Args:
            tile: Tile being resized.
            new_width: Target width.
            new_height: Target height.
        """
        if self.controller.resize_tile(tile, new_width, new_height):
            # Update widget geometry
            widget = self.tile_widgets.get(tile.instance_id)
            if widget:
                widget.update_geometry()
            
            self.layout_changed.emit()
            logger.info("Resized tile %s to %dx%d", tile.instance_id, new_width, new_height)
    
    def _on_tile_remove(self, tile: Tile) -> None:
        """Handle tile remove request.
        
        Args:
            tile: Tile to remove.
        """
        # Remove from controller
        self.controller.remove_tile(tile)
        
        # Remove widget
        widget = self.tile_widgets.pop(tile.instance_id, None)
        if widget:
            widget.deleteLater()
        
        self.layout_changed.emit()
        logger.info("Removed tile %s", tile.instance_id)
    
    def _on_tile_settings(self, tile: Tile) -> None:
        """Handle tile settings request.
        
        Args:
            tile: Tile to configure.
        """
        # Load schema for this plugin (or use default example schema)
        schema_loader = SchemaLoader()
        
        try:
            # Try to load plugin-specific schema
            schema_path = Path(__file__).parent.parent / "schema" / f"{tile.plugin_id}_settings.json"
            if schema_path.exists():
                schema = schema_loader.load_schema(schema_path)
            else:
                # Use example schema
                schema = schema_loader.load_schema_by_name("widget_settings_example.json")
        except Exception as e:
            logger.error("Failed to load schema: %s", e)
            QMessageBox.warning(
                self,
                "Settings Unavailable",
                f"Could not load settings schema for {tile.plugin_id}"
            )
            return
        
        # Get current settings from tile state
        current_settings = tile.state.get("settings", schema_loader.get_default_values(schema))
        
        # Show settings dialog
        dialog = SettingsDialog(
            schema,
            current_settings,
            title=f"{tile.plugin_id} Settings",
            parent=self
        )
        
        if dialog.exec():
            # Save settings to tile state
            tile.state["settings"] = dialog.get_settings()
            self.layout_changed.emit()
            logger.info("Updated settings for tile %s", tile.instance_id)
    
    def get_tiles(self) -> list[Tile]:
        """Get all tiles currently in the grid.
        
        Returns:
            List of tiles.
        """
        return self.controller.tiles.copy()
    
    def paintEvent(self, event) -> None:
        """Paint the grid overlay in edit mode.
        
        Args:
            event: Paint event.
        """
        super().paintEvent(event)
        
        if not self.is_edit_mode:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw grid lines
        pen = QPen(QColor("#E0E0E0"))
        pen.setWidth(1)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        # Vertical lines
        for col in range(1, self.GRID_COLS):
            x = col * self.cell_size
            painter.drawLine(x, 0, x, self.height())
        
        # Horizontal lines
        for row in range(1, self.GRID_ROWS):
            y = row * self.cell_size
            painter.drawLine(0, y, self.width(), y)
        
        # Draw grid border
        pen.setStyle(Qt.PenStyle.SolidLine)
        pen.setColor(QColor("#BDBDBD"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
    
    def resizeEvent(self, event) -> None:
        """Handle resize to maintain square cells.
        
        Args:
            event: Resize event.
        """
        super().resizeEvent(event)
        
        # Calculate cell size to fit
        available_width = self.width()
        available_height = self.height()
        
        cell_width = available_width / self.GRID_COLS
        cell_height = available_height / self.GRID_ROWS
        
        # Use smaller dimension to keep cells square
        self.cell_size = max(self.MIN_CELL_SIZE, min(cell_width, cell_height))
        
        # Update all tile geometries
        for widget in self.tile_widgets.values():
            widget.cell_size = self.cell_size
            widget.update_geometry()