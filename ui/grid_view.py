"""Grid view for displaying and managing widget tiles."""
from typing import Optional, Dict, List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QScrollArea, QPushButton
)
from PySide6.QtCore import Qt, Signal, QPoint, QRect, QSize, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
import logging

from core.grid_controller import GridController
from core.models import Tile, Page  # Correct names
from core.plugin_loader import PluginLoader
from ui.tile_widget import TileWidget
from ui.status_indicator import TileStatus

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
    
    def refresh(self) -> None:
        """Refresh the grid display with tiles from the current page only."""
        logger.info("=== GridView.refresh() called ===")
        
        # Clear existing tile widgets
        for tile_id, widget in list(self.tile_widgets.items()):
            logger.debug(f"Removing widget for tile {tile_id}")
            widget.hide()
            widget.deleteLater()
        self.tile_widgets.clear()
        
        # Check if we have a current page
        if not self.grid_controller.current_page:
            logger.warning("No current page set, cannot display tiles")
            self.update()
            return
        
        # Get current page info
        current_page = self.grid_controller.current_page
        current_page_id = current_page.id
        
        logger.info(f"Refreshing page '{current_page.name}' (ID: {current_page_id})")
        
        # Get tiles for CURRENT page only
        tiles = self.grid_controller.tiles_by_page.get(current_page_id, [])
        
        logger.info(f"Found {len(tiles)} tiles for current page")
        
        # If no tiles, just update and return
        if not tiles:
            logger.info("No tiles to display on current page")
            self.update()
            return
        
        # Track processed tile IDs to prevent duplicates
        processed_tile_ids = set()
        
        # Create and show widgets for each tile on current page
        for tile in tiles:
            # CRITICAL: Skip if already processed (duplicate)
            if tile.id in processed_tile_ids:
                logger.warning(f"Skipping duplicate tile {tile.id}")
                continue
            
            # CRITICAL: Double-check tile belongs to current page
            if tile.page_id != current_page_id:
                logger.warning(
                    f"Skipping tile {tile.id} - belongs to page {tile.page_id}, "
                    f"not current page {current_page_id}"
                )
                continue
            
            logger.info(
                f"Creating widget for tile {tile.id}: {tile.plugin_id} "
                f"at ({tile.row}, {tile.col})"
            )
            
            try:
                # Create tile widget
                tile_widget = self._create_tile_widget(tile)
                
                # Ensure parent is set
                tile_widget.setParent(self)
                
                # Set edit mode state
                tile_widget.set_edit_mode(self.edit_mode)
                
                # Update geometry to match tile position/size
                tile_widget.update_geometry()
                
                # Show the widget
                tile_widget.show()
                tile_widget.raise_()
                
                # Store in dictionary
                self.tile_widgets[tile.id] = tile_widget
                
                # Mark as processed
                processed_tile_ids.add(tile.id)
                
                logger.debug(
                    f"  Widget created: visible={tile_widget.isVisible()}, "
                    f"geometry={tile_widget.geometry()}"
                )
                
            except Exception as e:
                logger.error(
                    f"Error creating tile widget for {tile.id}: {e}",
                    exc_info=True
                )
        
        logger.info(
            f"Refresh complete: {len(self.tile_widgets)} widgets displayed "
            f"on page '{current_page.name}'"
        )
        
        # Force repaint
        self.update()
        self.repaint()

    def set_edit_mode(self, enabled: bool) -> None:
        """Enable or disable edit mode.
        
        Args:
            enabled: True to enable edit mode, False to disable
        """
        self.edit_mode = enabled
        
        logger.info(f"Grid edit mode: {enabled}")
        
        # Update all existing tile widgets
        for tile_widget in self.tile_widgets.values():
            tile_widget.set_edit_mode(enabled)
        
        # Trigger repaint to show/hide grid overlay
        self.update()


    
    def _create_tile_widget(self, tile: Tile) -> Optional[TileWidget]:
        """Create a tile widget for the given tile model."""
        try:
            logger.info(f"Creating widget for tile {tile.id}: {tile.plugin_id} at ({tile.row}, {tile.col})")
            
            # Get plugin instance
            plugin = self.plugin_loader.get_instance(tile.instance_id)
            
            if not plugin:
                logger.warning(f"No plugin instance found for {tile.instance_id}")
                return None
            
            # Create tile widget (handles both old and new signatures)
            tile_widget = TileWidget(tile, self.cell_size, self, plugin)
            
            # Connect signals
            tile_widget.settings_requested.connect(
                lambda tid=tile.id: self._on_tile_settings_requested(tid)
            )
            tile_widget.remove_requested.connect(
                lambda tid=tile.id: self._on_tile_remove_requested(tid)
            )
            
            # Request initial data from plugin
            try:
                tile_widget.set_status(TileStatus.UPDATING)
                response = plugin.update("resume")
                
                if response.get("status") == "ok" and "data" in response:
                    tile_widget.set_data(response["data"])
                else:
                    error_msg = response.get("error", "Failed to load")
                    logger.warning(f"Plugin returned error: {error_msg}")
                    tile_widget.set_status(TileStatus.ERROR, error_msg)
                    
            except Exception as e:
                logger.error(f"Error getting initial data: {e}")
                tile_widget.set_status(TileStatus.ERROR, "Load failed")
            
            return tile_widget
            
        except Exception as e:
            logger.error(f"Error creating tile widget for {tile.id}: {e}", exc_info=True)
            return None
    
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
    
    def _create_tile_widget(self, tile: Tile) -> Optional[TileWidget]:
        """Create a tile widget for the given tile model."""
        try:
            logger.info(f"Creating widget for tile {tile.id}: {tile.plugin_id} at ({tile.row}, {tile.col})")
            
            # Get plugin instance - check if plugin_loader exists
            plugin = None
            if hasattr(self, 'plugin_loader'):
                plugin = self.plugin_loader.get_instance(tile.instance_id)
            elif hasattr(self, '_plugin_loader'):
                plugin = self._plugin_loader.get_instance(tile.instance_id)
            else:
                # Try to get from parent (main_window)
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'plugin_loader'):
                        plugin = parent.plugin_loader.get_instance(tile.instance_id)
                        break
                    parent = parent.parent()
            
            if not plugin:
                logger.warning(f"No plugin instance found for {tile.instance_id}")
                return None
            
            # Create tile widget (handles both old and new signatures)
            tile_widget = TileWidget(tile, self.cell_size, self, plugin)
            
            # Connect signals if methods exist
            if hasattr(self, '_on_tile_settings_requested'):
                tile_widget.settings_requested.connect(
                    lambda tid=tile.id: self._on_tile_settings_requested(tid)
                )
            if hasattr(self, '_on_tile_remove_requested'):
                tile_widget.remove_requested.connect(
                    lambda tid=tile.id: self._on_tile_remove_requested(tid)
                )
            
            # Request initial data from plugin
            try:
                tile_widget.set_status(TileStatus.UPDATING)
                response = plugin.update("resume")
                
                if response.get("status") == "ok" and "data" in response:
                    tile_widget.set_data(response["data"])
                else:
                    error_msg = response.get("error", "Failed to load")
                    logger.warning(f"Plugin returned error: {error_msg}")
                    tile_widget.set_status(TileStatus.ERROR, error_msg)
                    
            except Exception as e:
                logger.error(f"Error getting initial data: {e}")
                tile_widget.set_status(TileStatus.ERROR, "Load failed")
            
            return tile_widget
            
        except Exception as e:
            logger.error(f"Error creating tile widget for {tile.id}: {e}", exc_info=True)
            return None