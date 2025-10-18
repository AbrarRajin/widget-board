"""Visual widget for displaying tiles with plugin support."""

import logging
from typing import Optional
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QTextEdit
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from core.models import Tile
from core.plugin_api import WidgetPlugin  # Changed from PluginBase to WidgetPlugin

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
        plugin: Optional[WidgetPlugin] = None  # Changed from PluginBase
    ) -> None:
        """Initialize tile widget.
        
        Args:
            tile: The tile data model
            cell_size: Size of one grid cell in pixels
            parent: Parent widget
            plugin: Optional plugin instance to render in the tile
        """
        super().__init__(parent)
        
        self.tile = tile
        self.cell_size = cell_size
        self.plugin = plugin
        self.is_edit_mode = False
        self.is_dragging = False
        self.is_resizing = False
        self.drag_start_pos = QPoint()
        self.start_geometry = QRect()
        self.content_widget = None
        
        # Update timer for plugins that need periodic updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._on_update_timer)
        self.last_update_time = 0
        
        self._setup_ui()
        self.update_geometry()
        
        # Connect to plugin signals if available
        if self.plugin:
            self.plugin.render_updated.connect(self._refresh_content)
    
    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        # Widget properties
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Create content widget
        self._create_content_widget(layout)
        
        # Apply initial style
        self._update_style()
    
    def _create_content_widget(self, layout: QVBoxLayout) -> None:
        """Create the content widget based on plugin availability.
        print(f"DEBUG: Creating content for tile {self.tile.instance_id}")
        print(f"  Plugin: {self.plugin}")
        print(f"  Plugin ID: {self.tile.plugin_id}")
        
        Args:
            layout: The layout to add content to
        """
        # Check if we have a plugin to render
        if self.plugin:
            print(f"  Plugin state: {self.plugin.state}")
            try:
                # Get render data from plugin
                render_data = self.plugin.get_render_data()
                print(f"  Render data: {render_data}")
                
                if "html" in render_data:
                    # Create HTML display widget
                    self.content_widget = QTextEdit()
                    self.content_widget.setReadOnly(True)
                    self.content_widget.setFrameStyle(0)
                    self.content_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                    self.content_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                    self.content_widget.setHtml(render_data["html"])
                    layout.addWidget(self.content_widget, 1)
                    
                    # Start update timer if plugin needs updates
                    if render_data.get("needs_update", False):
                        self.update_timer.start(16)  # ~60 FPS
                else:
                    # No HTML, show placeholder
                    self._create_placeholder_content(layout)
                    
            except Exception as e:
                logger.error(f"Error getting render data from plugin: {e}", exc_info=True)
                # Show error message in tile
                error_label = QLabel(f"Plugin Error:\n{str(e)}")
                error_label.setStyleSheet("color: red;")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(error_label)
        else:
            # No plugin - show placeholder content
            self._create_placeholder_content(layout)
    
    def _create_placeholder_content(self, layout: QVBoxLayout) -> None:
        """Create placeholder content when no plugin is available.
        
        Args:
            layout: The layout to add content to
        """
        # Title label
        self.title_label = QLabel(self.tile.plugin_id or "Empty Tile")
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
    
    def _on_update_timer(self) -> None:
        """Handle update timer tick."""
        if not self.plugin:
            self.update_timer.stop()
            return
        
        # Calculate delta time
        import time
        current_time = time.time()
        if self.last_update_time == 0:
            delta_time = 0.016  # ~60 FPS
        else:
            delta_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Update plugin
        try:
            self.plugin.update(delta_time)
        except Exception as e:
            logger.error(f"Error updating plugin: {e}")
    
    def _refresh_content(self) -> None:
        """Refresh the content from the plugin."""
        if not self.plugin or not self.content_widget:
            return
        
        try:
            render_data = self.plugin.get_render_data()
            if "html" in render_data and isinstance(self.content_widget, QTextEdit):
                self.content_widget.setHtml(render_data["html"])
        except Exception as e:
            logger.error(f"Error refreshing content: {e}")
    
    def set_plugin(self, plugin: Optional[WidgetPlugin]) -> None:
        """Set or update the plugin for this tile.
        
        Args:
            plugin: New plugin instance, or None to clear
        """
        # Disconnect old plugin signals
        if self.plugin:
            try:
                self.plugin.render_updated.disconnect(self._refresh_content)
            except:
                pass
        
        self.plugin = plugin
        
        # Connect new plugin signals
        if self.plugin:
            self.plugin.render_updated.connect(self._refresh_content)
        
        # Rebuild the UI
        self._clear_layout()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self._create_content_widget(layout)
        self._update_style()
    
    def _clear_layout(self) -> None:
        """Clear all widgets from the layout."""
        # Stop update timer
        self.update_timer.stop()
        
        # Clear layout
        if self.layout():
            while self.layout().count():
                item = self.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Delete the layout itself
            self.layout().deleteLater()
    
    def set_edit_mode(self, enabled: bool) -> None:
        """Set edit mode on or off.
        
        Args:
            enabled: True to enable edit mode
        """
        self.is_edit_mode = enabled
        self._update_style()
        self.update()
    
    def update_geometry(self) -> None:
        """Update widget geometry based on tile position and size."""
        x = self.tile.col * self.cell_size
        y = self.tile.row * self.cell_size
        width = self.tile.width * self.cell_size
        height = self.tile.height * self.cell_size
        
        self.setGeometry(x, y, width, height)
    
    def _update_style(self) -> None:
        """Update widget styling based on state."""
        if self.is_edit_mode:
            self.setStyleSheet("""
                TileWidget {
                    background-color: white;
                    border: 2px solid #2196F3;
                    border-radius: 4px;
                }
                TileWidget:hover {
                    border-color: #1976D2;
                }
            """)
        else:
            self.setStyleSheet("""
                TileWidget {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
            """)
    
    def paintEvent(self, event):
        """Paint the widget."""
        super().paintEvent(event)
        
        # Draw resize handle in edit mode
        if self.is_edit_mode:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Resize handle
            handle_rect = self._get_resize_handle_rect()
            painter.fillRect(handle_rect, QColor("#2196F3"))
            
            # Draw grip lines
            painter.setPen(QPen(QColor("white"), 2))
            grip_offset = 3
            painter.drawLine(
                handle_rect.right() - grip_offset,
                handle_rect.bottom() - grip_offset - 6,
                handle_rect.right() - grip_offset,
                handle_rect.bottom() - grip_offset
            )
            painter.drawLine(
                handle_rect.right() - grip_offset - 6,
                handle_rect.bottom() - grip_offset,
                handle_rect.right() - grip_offset,
                handle_rect.bottom() - grip_offset
            )
    
    def _get_resize_handle_rect(self) -> QRect:
        """Get the resize handle rectangle."""
        return QRect(
            self.width() - self.RESIZE_HANDLE_SIZE,
            self.height() - self.RESIZE_HANDLE_SIZE,
            self.RESIZE_HANDLE_SIZE,
            self.RESIZE_HANDLE_SIZE
        )
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if not self.is_edit_mode:
            return
        
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking resize handle
            if self._get_resize_handle_rect().contains(event.pos()):
                self.is_resizing = True
                self.drag_start_pos = event.pos()
                self.resize_start_width = self.tile.width
                self.resize_start_height = self.tile.height
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                event.accept()
            else:
                self.is_dragging = True
                self.drag_start_pos = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move."""
        if not self.is_edit_mode:
            return
        
        # Update cursor based on position
        if not self.is_dragging and not self.is_resizing:
            if self._get_resize_handle_rect().contains(event.pos()):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        # Handle dragging
        if self.is_dragging:
            delta = event.pos() - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()
            
            # Snap to grid
            new_col = round(new_x / self.cell_size)
            new_row = round(new_y / self.cell_size)
            
            # Clamp to grid bounds
            new_col = max(0, min(7 - self.tile.width + 1, new_col))
            new_row = max(0, min(7 - self.tile.height + 1, new_row))
            
            if new_col != self.tile.col or new_row != self.tile.row:
                self.move_requested.emit(new_row, new_col)
        
        # Handle resizing - FIXED VERSION
        elif self.is_resizing:
            # Calculate total delta from start of resize
            delta = event.pos() - self.drag_start_pos
            
            # Calculate how many cells we've moved (using larger threshold for better feel)
            cells_x = round(delta.x() / self.cell_size)
            cells_y = round(delta.y() / self.cell_size)
            
            # Calculate new size
            new_width = self.resize_start_width + cells_x
            new_height = self.resize_start_height + cells_y
            
            # Clamp to valid range (minimum 1, maximum to grid edge)
            max_width = 8 - self.tile.col
            max_height = 8 - self.tile.row
            new_width = max(1, min(max_width, new_width))
            new_height = max(1, min(max_height, new_height))
            
            # Only emit if size actually changed
            if new_width != self.tile.width or new_height != self.tile.height:
                self.resize_requested.emit(new_width, new_height)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.is_resizing = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
    
    def closeEvent(self, event):
        """Handle widget close event."""
        # Stop update timer
        self.update_timer.stop()
        
        # Disconnect plugin signals
        if self.plugin:
            try:
                self.plugin.render_updated.disconnect(self._refresh_content)
            except:
                pass
        
        super().closeEvent(event)