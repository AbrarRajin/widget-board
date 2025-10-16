"""Visual widget for displaying tiles with plugin support."""

import logging
from typing import Optional
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from core.models import Tile
from core.plugin_api import PluginBase

logger = logging.getLogger(__name__)


class TileWidget(QWidget):
    """Visual representation of a grid tile with plugin rendering support."""
    
    # Signals
    move_requested = Signal(int, int)  # row, col
    resize_requested = Signal(int, int)  # width, height
    remove_requested = Signal()
    
    # Visual constants
    RESIZE_HANDLE_SIZE = 12
    BORDER_WIDTH = 2
    
    def __init__(
        self,
        tile: Tile,
        cell_size: int,
        parent: Optional[QWidget] = None,
        plugin: Optional[PluginBase] = None
    ) -> None:
        """Initialize tile widget.
        
        Args:
            tile: The tile data model.
            cell_size: Size of one grid cell in pixels.
            parent: Parent widget.
            plugin: Optional plugin instance to render in the tile.
        """
        super().__init__(parent)
        
        self.tile = tile
        self.cell_size = cell_size
        self.plugin = plugin
        self.is_edit_mode = False
        self.is_dragging = False
        self.is_resizing = False
        self.drag_start_pos = QPoint()
        
        self._setup_ui()
        self.update_geometry()
    
    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        # Widget properties
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Check if we have a plugin to render
        if self.plugin:
            try:
                # Get the plugin's widget and add it to our layout
                plugin_widget = self.plugin.get_widget()
                layout.addWidget(plugin_widget, 1)  # Stretch factor 1
            except Exception as e:
                logger.error(f"Error getting widget from plugin: {e}")
                # Show error message in tile
                error_label = QLabel(f"Plugin Error:\n{str(e)}")
                error_label.setStyleSheet("color: red;")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(error_label)
        else:
            # No plugin - show placeholder content
            self._create_placeholder_content(layout)
        
        # Apply initial style
        self._update_style()
    
    def _create_placeholder_content(self, layout: QVBoxLayout) -> None:
        """Create placeholder content when no plugin is available.
        
        Args:
            layout: The layout to add content to.
        """
        # Title label
        self.title_label = QLabel(self.tile.plugin_id)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        self.title_label.setFont(font)
        
        # Info label
        self.info_label = QLabel(f"{self.tile.width}×{self.tile.height}")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: #666;")
        
        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addWidget(self.info_label)
        layout.addStretch()
    
    def set_plugin(self, plugin: Optional[PluginBase]) -> None:
        """Set or update the plugin for this tile.
        
        Args:
            plugin: New plugin instance, or None to clear.
        """
        # Stop old plugin if exists
        if self.plugin:
            try:
                self.plugin.stop()
            except Exception as e:
                logger.error(f"Error stopping old plugin: {e}")
        
        self.plugin = plugin
        
        # Rebuild UI
        self._clear_layout()
        self._setup_ui()
        
        # Start new plugin if exists
        if self.plugin:
            try:
                self.plugin.start()
            except Exception as e:
                logger.error(f"Error starting new plugin: {e}")
    
    def _clear_layout(self) -> None:
        """Clear all widgets from the layout."""
        layout = self.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
    
    def set_edit_mode(self, enabled: bool) -> None:
        """Enable or disable edit mode.
        
        Args:
            enabled: True to enable edit mode.
        """
        self.is_edit_mode = enabled
        self.setCursor(Qt.CursorShape.OpenHandCursor if enabled else Qt.CursorShape.ArrowCursor)
        self._update_style()
        self.update()
    
    def update_geometry(self) -> None:
        """Update widget geometry based on tile position and size."""
        x = self.tile.col * self.cell_size
        y = self.tile.row * self.cell_size
        w = self.tile.width * self.cell_size
        h = self.tile.height * self.cell_size
        
        self.setGeometry(x, y, w, h)
    
    def _update_style(self) -> None:
        """Update widget styling based on current state."""
        if self.is_edit_mode:
            # Edit mode: blue tinted background
            self.setStyleSheet("""
                TileWidget {
                    background-color: rgba(33, 150, 243, 0.1);
                    border: 2px solid #2196F3;
                    border-radius: 4px;
                }
            """)
        else:
            # View mode: white/dark background
            self.setStyleSheet("""
                TileWidget {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
            """)
    
    def paintEvent(self, event) -> None:
        """Paint the widget."""
        super().paintEvent(event)
        
        # Draw resize handle in edit mode
        if self.is_edit_mode:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw resize handle in bottom-right corner
            handle_rect = self._get_resize_handle_rect()
            painter.fillRect(handle_rect, QColor(33, 150, 243))
            
            painter.end()
    
    def _get_resize_handle_rect(self) -> QRect:
        """Get the rectangle for the resize handle.
        
        Returns:
            QRect for the resize handle.
        """
        size = self.RESIZE_HANDLE_SIZE
        x = self.width() - size
        y = self.height() - size
        return QRect(x, y, size, size)
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press."""
        if not self.is_edit_mode:
            return
        
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking resize handle
            if self._get_resize_handle_rect().contains(event.pos()):
                self.is_resizing = True
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.is_dragging = True
                self.drag_start_pos = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move."""
        if not self.is_edit_mode:
            return
        
        # Update cursor based on position
        if not self.is_dragging and not self.is_resizing:
            if self._get_resize_handle_rect().contains(event.pos()):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_dragging:
                # Calculate new position
                delta = event.pos() - self.drag_start_pos
                new_row = self.tile.row + round(delta.y() / self.cell_size)
                new_col = self.tile.col + round(delta.x() / self.cell_size)
                
                # Emit move request
                self.move_requested.emit(new_row, new_col)
                
                self.is_dragging = False
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            
            elif self.is_resizing:
                # Calculate new size
                new_width = max(1, round(event.x() / self.cell_size))
                new_height = max(1, round(event.y() / self.cell_size))
                
                # Emit resize request
                self.resize_requested.emit(new_width, new_height)
                
                self.is_resizing = False
                self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def keyPressEvent(self, event) -> None:
        """Handle key press events."""
        if not self.is_edit_mode:
            return
        
        # Arrow keys for moving
        if event.key() == Qt.Key.Key_Up:
            self.move_requested.emit(self.tile.row - 1, self.tile.col)
        elif event.key() == Qt.Key.Key_Down:
            self.move_requested.emit(self.tile.row + 1, self.tile.col)
        elif event.key() == Qt.Key.Key_Left:
            self.move_requested.emit(self.tile.row, self.tile.col - 1)
        elif event.key() == Qt.Key.Key_Right:
            self.move_requested.emit(self.tile.row, self.tile.col + 1)
        
        # Shift+Arrow keys for resizing
        elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            if event.key() == Qt.Key.Key_Up:
                self.resize_requested.emit(self.tile.width, self.tile.height - 1)
            elif event.key() == Qt.Key.Key_Down:
                self.resize_requested.emit(self.tile.width, self.tile.height + 1)
            elif event.key() == Qt.Key.Key_Left:
                self.resize_requested.emit(self.tile.width - 1, self.tile.height)
            elif event.key() == Qt.Key.Key_Right:
                self.resize_requested.emit(self.tile.width + 1, self.tile.height)
        
        # Delete key for removing
        elif event.key() == Qt.Key.Key_Delete:
            self.remove_requested.emit()
    
    def focusInEvent(self, event) -> None:
        """Handle focus in event."""
        super().focusInEvent(event)
        if self.is_edit_mode:
            # Highlight when focused
            self.setStyleSheet("""
                TileWidget {
                    background-color: rgba(33, 150, 243, 0.2);
                    border: 2px solid #1976D2;
                    border-radius: 4px;
                }
            """)
    
    def focusOutEvent(self, event) -> None:
        """Handle focus out event."""
        super().focusOutEvent(event)
        self._update_style()