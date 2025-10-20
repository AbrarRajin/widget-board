"""Tile widget with chrome (titlebar, status, menu) and content area."""
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
)
from PySide6.QtCore import Qt, Signal, QPoint, QRect, QTimer
from PySide6.QtGui import QPainter, QColor, QPen
import logging

from ui.status_indicator import StatusIndicator, TileStatus
from ui.tile_menu import TileMenu
from ui.data_renderers import DataRenderer

logger = logging.getLogger(__name__)


class TileWidget(QFrame):
    """
    Complete tile widget with chrome and content.
    
    Structure:
    - Title bar (drag handle, title, status, menu)
    - Content area (rendered from plugin data)
    - Resize handles (in edit mode)
    
    Compatible with both old (M1-M4) and new (M5) initialization.
    """
    
    # Signals
    drag_started = Signal(QPoint)
    settings_requested = Signal()
    refresh_requested = Signal()
    remove_requested = Signal()
    duplicate_requested = Signal()
    resize_started = Signal(QPoint)
    
    def __init__(self, *args, **kwargs):
        """
        Flexible constructor supporting both signatures:
        - New: TileWidget(instance_id: str, plugin_name: str, parent: QWidget)
        - Old: TileWidget(tile: TileModel, cell_size: int, parent: QWidget, plugin: PluginProxy)
        """
        # Parse arguments
        if len(args) >= 2 and isinstance(args[1], int):
            # Old signature: (tile, cell_size, parent, plugin)
            tile = args[0]
            cell_size = args[1]
            parent = args[2] if len(args) > 2 else kwargs.get('parent')
            plugin = args[3] if len(args) > 3 else kwargs.get('plugin')
            
            super().__init__(parent)
            
            self.tile = tile
            self.instance_id = tile.instance_id
            self.plugin_name = tile.plugin_id  # Use plugin_id from tile
            self.plugin = plugin
            self.cell_size = cell_size
            
            # Get actual plugin name if plugin proxy is available
            if plugin and hasattr(plugin, 'manifest'):
                self.plugin_name = plugin.manifest.get('name', tile.plugin_id)
        else:
            # New signature: (instance_id, plugin_name, parent)
            instance_id = args[0] if len(args) > 0 else kwargs.get('instance_id')
            plugin_name = args[1] if len(args) > 1 else kwargs.get('plugin_name')
            parent = args[2] if len(args) > 2 else kwargs.get('parent')
            
            super().__init__(parent)
            
            self.instance_id = instance_id
            self.plugin_name = plugin_name
            self.tile = None
            self.plugin = None
            self.cell_size = 100  # Default
        
        self._edit_mode = False
        self._is_dragging = False
        self._is_resizing = False
        self._drag_start_pos: Optional[QPoint] = None
        self._resize_start_pos: Optional[QPoint] = None
        
        self._setup_ui()
        self._apply_style()
        
        # Auto-refresh timer for plugin updates
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh)
        
    def set_plugin(self, plugin) -> None:
        """Set plugin proxy (for compatibility with grid_view)."""
        self.plugin = plugin
        if plugin and hasattr(plugin, 'manifest'):
            self.plugin_name = plugin.manifest.get('name', self.plugin_name)
            self._title_label.setText(self.plugin_name)
            
            # Start auto-refresh if plugin has refresh cadence
            cadence = plugin.manifest.get('refresh_cadence_ms', 0)
            if cadence > 0:
                self._refresh_timer.start(cadence)
    
    def _setup_ui(self) -> None:
        """Build the tile UI structure."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Title bar
        self._title_bar = QWidget()
        self._title_bar.setFixedHeight(36)
        title_layout = QHBoxLayout(self._title_bar)
        title_layout.setContentsMargins(12, 6, 8, 6)
        title_layout.setSpacing(8)
        
        # Drag handle (visible in edit mode)
        self._drag_handle = QLabel("⋮⋮")
        self._drag_handle.setFixedSize(16, 24)
        self._drag_handle.setStyleSheet("color: #999; font-weight: bold;")
        self._drag_handle.setVisible(False)
        title_layout.addWidget(self._drag_handle)
        
        # Title
        self._title_label = QLabel(self.plugin_name)
        self._title_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        title_layout.addWidget(self._title_label, 1)
        
        # Status indicator
        self._status_indicator = StatusIndicator()
        title_layout.addWidget(self._status_indicator)
        
        # Menu
        self._menu = TileMenu()
        self._menu.settings_requested.connect(self.settings_requested.emit)
        self._menu.refresh_requested.connect(self._on_refresh_requested)
        self._menu.remove_requested.connect(self.remove_requested.emit)
        self._menu.duplicate_requested.connect(self.duplicate_requested.emit)
        title_layout.addWidget(self._menu)
        
        main_layout.addWidget(self._title_bar)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: #e0e0e0;")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Content area
        self._content_container = QWidget()
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._content_container, 1)
        
        # Initial status
        self._set_placeholder()
        self.set_status(TileStatus.STARTING, "Initializing")
    
    def _apply_style(self) -> None:
        """Apply styling to the tile."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            TileWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            TileWidget:hover {
                border: 1px solid #bdbdbd;
            }
        """)
    
    def set_edit_mode(self, enabled: bool) -> None:
        """Toggle edit mode (show drag handle, enable dragging)."""
        self._edit_mode = enabled
        self._drag_handle.setVisible(enabled)
        
        if enabled:
            self._title_bar.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self._title_bar.setCursor(Qt.CursorShape.ArrowCursor)
    
    def set_status(self, status: TileStatus, message: str = "") -> None:
        """Update tile status indicator."""
        self._status_indicator.set_status(status, message)
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """
        Update tile content from plugin data.
        
        Expected data format:
        {
            "layout": "text" | "metric" | "list" | "key_value" | "header_body",
            "content": {...}
        }
        """
        try:
            # Remove old content
            while self._content_layout.count():
                item = self._content_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Render new content
            content_widget = DataRenderer.render(data, self._content_container)
            self._content_layout.addWidget(content_widget)
            
            # Update status to OK
            self.set_status(TileStatus.OK)
            
            logger.debug(f"Rendered data for {self.instance_id}: {data.get('layout', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error rendering data for {self.instance_id}: {e}")
            self._set_error(str(e))
            self.set_status(TileStatus.ERROR, "Render failed")
    
    def _set_placeholder(self) -> None:
        """Show placeholder content."""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        placeholder = QLabel("Loading...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #999;")
        self._content_layout.addWidget(placeholder)
    
    def _set_error(self, message: str) -> None:
        """Show error message in content area."""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        error_label = QLabel(f"⚠ Error\n{message}")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setWordWrap(True)
        error_label.setStyleSheet("color: #F44336; padding: 20px;")
        self._content_layout.addWidget(error_label)
    
    def _auto_refresh(self) -> None:
        """Auto-refresh from plugin."""
        if self.plugin:
            try:
                self.set_status(TileStatus.UPDATING)
                response = self.plugin.update("timer")
                
                if response.get("status") == "ok" and "data" in response:
                    self.set_data(response["data"])
                else:
                    error_msg = response.get("error", "Unknown error")
                    self._set_error(error_msg)
                    self.set_status(TileStatus.ERROR, error_msg)
            except Exception as e:
                logger.error(f"Auto-refresh failed for {self.instance_id}: {e}")
                self._set_error(str(e))
                self.set_status(TileStatus.ERROR, "Update failed")
    
    def _on_refresh_requested(self) -> None:
        """Handle manual refresh request."""
        self.refresh_requested.emit()
        if self.plugin:
            self._auto_refresh()
    
    def refresh_from_plugin(self) -> None:
        """Force refresh from plugin (called externally)."""
        self._auto_refresh()
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press for dragging and resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check for resize handle
            if self._edit_mode and self._is_over_resize_handle(event.pos()):
                self._is_resizing = True
                self._resize_start_pos = event.pos()
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                self.resize_started.emit(event.globalPosition().toPoint())
                event.accept()
                return
            
            # Check for drag in title bar
            if self._edit_mode and self._title_bar.geometry().contains(event.pos()):
                self._is_dragging = True
                self._drag_start_pos = event.pos()
                self._title_bar.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.drag_started.emit(event.globalPosition().toPoint())
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release."""
        if self._is_dragging:
            self._is_dragging = False
            self._drag_start_pos = None
            if self._edit_mode:
                self._title_bar.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
            return
        
        if self._is_resizing:
            self._is_resizing = False
            self._resize_start_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for resize handle cursor."""
        if self._edit_mode and self._is_over_resize_handle(event.pos()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif not self._is_resizing:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        
        super().mouseMoveEvent(event)
    
    def _is_over_resize_handle(self, pos: QPoint) -> bool:
        """Check if position is over the resize handle."""
        handle_size = 16
        handle_rect = QRect(
            self.width() - handle_size,
            self.height() - handle_size,
            handle_size,
            handle_size
        )
        return handle_rect.contains(pos)
    
    def paintEvent(self, event) -> None:
        """Custom paint for selection/hover effects."""
        super().paintEvent(event)
        
        # Draw resize handles in edit mode
        if self._edit_mode:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Bottom-right corner handle
            handle_size = 12
            handle_rect = QRect(
                self.width() - handle_size - 4,
                self.height() - handle_size - 4,
                handle_size,
                handle_size
            )
            
            painter.setPen(QPen(QColor("#999"), 2))
            painter.drawLine(
                handle_rect.topRight(),
                handle_rect.bottomLeft()
            )
            painter.drawLine(
                handle_rect.topRight() + QPoint(-4, 4),
                handle_rect.bottomLeft() + QPoint(-4, 4)
            )