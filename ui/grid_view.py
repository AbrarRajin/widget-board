"""Grid view - displays the 8×8 tile grid with plugin rendering support."""

import logging
from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Qt, Signal, QPoint, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QPen

from core.models import Tile
from core.grid_controller import GridController
from ui.tile_widget import TileWidget
from ui.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class GridView(QWidget):
    """8×8 grid view for displaying and interacting with tiles."""
    
    # Signals
    layout_changed = Signal()
    
    # Grid constants
    GRID_ROWS = 8
    GRID_COLS = 8
    MIN_CELL_SIZE = 80
    DEFAULT_CELL_SIZE = 120
    
    def __init__(self, grid_controller: GridController, parent: Optional[QWidget] = None) -> None:
        """Initialize grid view.
        
        Args:
            grid_controller: The grid controller managing tiles.
            parent: Parent widget (should be MainWindow).
        """
        super().__init__(parent)
        
        self.grid_controller = grid_controller
        self.edit_mode = False
        self.cell_size = self.DEFAULT_CELL_SIZE
        
        # Tile widgets mapping
        self.tile_widgets: Dict[int, TileWidget] = {}  # tile.id -> TileWidget
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the grid view UI."""
        self.setMinimumSize(
            self.GRID_COLS * self.MIN_CELL_SIZE,
            self.GRID_ROWS * self.MIN_CELL_SIZE
        )
        self.resize(
            self.GRID_COLS * self.cell_size,
            self.GRID_ROWS * self.cell_size
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def set_edit_mode(self, enabled: bool) -> None:
        """Enable or disable edit mode.
        
        Args:
            enabled: True to enable edit mode.
        """
        self.edit_mode = enabled
        
        # Update all tile widgets
        for tile_widget in self.tile_widgets.values():
            tile_widget.set_edit_mode(enabled)
        
        self.update()
        logger.info(f"Grid edit mode: {enabled}")
    
    def refresh(self) -> None:
        """Refresh the grid display with current tiles."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("=== GridView.refresh() called ===")
        
        # Clear existing tile widgets
        for tile_id, widget in list(self.tile_widgets.items()):
            logger.debug(f"Removing old widget for tile {tile_id}")
            widget.hide()
            widget.deleteLater()
        self.tile_widgets.clear()
        
        # Get tiles for current page (use property, not method)
        tiles = self.grid_controller.tiles  # Changed from get_current_tiles()
        logger.info(f"Found {len(tiles)} tiles for current page")
        
        if not tiles:
            logger.warning("No tiles to display")
            self.update()
            return
        
        # Create and show widgets for each tile
        for tile in tiles:
            logger.info(f"Creating widget for tile {tile.id}: {tile.plugin_id} at ({tile.row}, {tile.col})")
            
            try:
                # Create tile widget
                tile_widget = self._create_tile_widget(tile)
                
                # Set parent explicitly
                tile_widget.setParent(self)
                
                # Update geometry
                tile_widget.update_geometry()
                
                # Show the widget
                tile_widget.show()
                tile_widget.raise_()
                
                # Store in dictionary
                self.tile_widgets[tile.id] = tile_widget
                
                logger.info(f"  Widget created: visible={tile_widget.isVisible()}, geometry={tile_widget.geometry()}")
                
            except Exception as e:
                logger.error(f"Error creating tile widget for {tile.id}: {e}", exc_info=True)
        
        logger.info(f"Refresh complete: {len(self.tile_widgets)} widgets displayed")
        
        # Force update
        self.update()
        self.repaint()
    
    def _create_tile_widget(self, tile: Tile) -> TileWidget:
        """Create a visual widget for a tile.
        
        Args:
            tile: The tile model.
        
        Returns:
            TileWidget instance.
        """
        # Get plugin instance if exists
        plugin = None
        if hasattr(self.parent(), 'plugin_loader'):
            plugin = self.parent().plugin_loader.get_instance(tile.instance_id)
        
        # Create tile widget with plugin
        tile_widget = TileWidget(tile, self.cell_size, self, plugin)
        tile_widget.set_edit_mode(self.edit_mode)
        
        # Connect signals
        tile_widget.move_requested.connect(
            lambda r, c, t=tile: self._handle_move_request(t, r, c)
        )
        tile_widget.resize_requested.connect(
            lambda w, h, t=tile: self._handle_resize_request(t, w, h)
        )
        tile_widget.remove_requested.connect(
            lambda t=tile: self._handle_remove_request(t)
        )
        


        
        return tile_widget
    
    def _handle_move_request(self, tile: Tile, new_row: int, new_col: int) -> None:
        """Handle tile move request.
        
        Args:
            tile: The tile to move.
            new_row: New row position.
            new_col: New column position.
        """
        if self.grid_controller.move_tile(tile.id, new_row, new_col):
            # Update tile widget
            if tile.id in self.tile_widgets:
                self.tile_widgets[tile.id].update_geometry()
            
            # Emit signal to save changes
            self.layout_changed.emit()
            logger.debug(f"Moved tile {tile.id} to ({new_row}, {new_col})")
        else:
            # Move failed (collision or out of bounds)
            logger.debug(f"Move failed for tile {tile.id} to ({new_row}, {new_col})")
    
    def _handle_resize_request(self, tile: Tile, new_width: int, new_height: int) -> None:
        """Handle tile resize request.
        
        Args:
            tile: The tile to resize.
            new_width: New width in grid cells.
            new_height: New height in grid cells.
        """
        if self.grid_controller.resize_tile(tile.id, new_width, new_height):
            # Update tile widget
            if tile.id in self.tile_widgets:
                self.tile_widgets[tile.id].update_geometry()
            
            # Emit signal to save changes
            self.layout_changed.emit()
            logger.debug(f"Resized tile {tile.id} to {new_width}×{new_height}")
        else:
            # Resize failed (collision or invalid size)
            logger.debug(f"Resize failed for tile {tile.id} to {new_width}×{new_height}")
    
    def _handle_remove_request(self, tile: Tile) -> None:
        """Handle tile removal request.
        
        Args:
            tile: The tile to remove.
        """
        reply = QMessageBox.question(
            self,
            "Remove Tile",
            f"Remove tile '{tile.plugin_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Destroy plugin instance
            if hasattr(self.parent(), 'plugin_loader'):
                self.parent().plugin_loader.destroy_instance(tile.instance_id)
            
            # Delete from database
            if hasattr(self.parent(), 'repository') and tile.id is not None:
                self.parent().repository.delete_tile(tile.id)
            
            # Remove from grid controller
            self.grid_controller.remove_tile(tile.id)
            
            # Remove widget
            if tile.id in self.tile_widgets:
                self.tile_widgets[tile.id].deleteLater()
                del self.tile_widgets[tile.id]
            
            # Emit signal (for any additional cleanup)
            self.layout_changed.emit()
            logger.info(f"Removed tile {tile.id}")
    
    def paintEvent(self, event) -> None:
        """Paint the grid."""
        super().paintEvent(event)
        
        if not self.edit_mode:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw grid lines
        pen = QPen(QColor(200, 200, 200))
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        # Vertical lines
        for col in range(self.GRID_COLS + 1):
            x = col * self.cell_size
            painter.drawLine(x, 0, x, self.height())
        
        # Horizontal lines
        for row in range(self.GRID_ROWS + 1):
            y = row * self.cell_size
            painter.drawLine(0, y, self.width(), y)
        
        painter.end()
    
    def contextMenuEvent(self, event) -> None:
        """Handle right-click context menu.
        
        Args:
            event: Context menu event.
        """
        if not self.edit_mode:
            return
        
        # Find which tile was clicked
        pos = event.pos()
        clicked_tile = None
        
        for tile_id, tile_widget in self.tile_widgets.items():
            if tile_widget.geometry().contains(pos):
                clicked_tile = tile_widget.tile
                break
        
        if not clicked_tile:
            return
        
        # Show settings dialog
        self._show_tile_settings(clicked_tile)
    
    def _show_tile_settings(self, tile: Tile) -> None:
        """Show settings dialog for a tile.
        
        Args:
            tile: The tile to configure.
        """
        # Get plugin metadata
        metadata = None
        if hasattr(self.parent(), 'plugin_loader'):
            metadata = self.parent().plugin_loader.get_metadata(tile.plugin_id)
        
        if not metadata or not metadata.schema_path:
            QMessageBox.information(
                self,
                "No Settings",
                f"The '{tile.plugin_id}' plugin has no configurable settings."
            )
            return
        
        # Show settings dialog
        dialog = SettingsDialog(
            title=f"{metadata.name} Settings",
            schema_path=metadata.schema_path,
            current_values=tile.state,
            parent=self
        )
        
        if dialog.exec():
            new_settings = dialog.get_values()
            
            # Update tile state
            tile.state = new_settings
            
            # Update plugin instance
            if hasattr(self.parent(), 'plugin_loader'):
                self.parent().plugin_loader.update_instance(
                    tile.instance_id,
                    new_settings
                )
            
            # Save to database
            if hasattr(self.parent(), 'repository'):
                self.parent().repository.update_tile(tile)
            
            logger.info(f"Updated settings for tile {tile.id}")
    
    def sizeHint(self) -> QSize:
        """Get the recommended size for the grid.
        
        Returns:
            Recommended size.
        """
        return QSize(
            self.GRID_COLS * self.cell_size,
            self.GRID_ROWS * self.cell_size
        )