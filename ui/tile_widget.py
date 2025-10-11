"""Visual widget for displaying tiles."""

import logging
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QMenu
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QAction

from core.models import Tile

logger = logging.getLogger(__name__)


class TileWidget(QWidget):
    """Visual representation of a grid tile."""
    
    # Signals
    move_requested = Signal(int, int)  # row, col
    resize_requested = Signal(int, int)  # width, height
    remove_requested = Signal()
    settings_requested = Signal()  # New signal for settings
    
    # Visual constants
    RESIZE_HANDLE_SIZE = 12
    BORDER_WIDTH = 2
    
    def __init__(self, tile: Tile, cell_size: int, parent=None) -> None:
        """Initialize tile widget.
        
        Args:
            tile: The tile data model.
            cell_size: Size of one grid cell in pixels.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.tile = tile
        self.cell_size = cell_size
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
        
        # Apply initial style
        self._update_style()
    
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
        width = self.tile.width * self.cell_size
        height = self.tile.height * self.cell_size
        
        self.setGeometry(x, y, width, height)
        self.info_label.setText(f"{self.tile.width}×{self.tile.height}")
    
    def _update_style(self) -> None:
        """Update widget styling based on state."""
        if self.is_edit_mode:
            bg_color = "#E3F2FD"
            border_color = "#2196F3"
        else:
            bg_color = "#FAFAFA"
            border_color = "#E0E0E0"
        
        self.setStyleSheet(f"""
            TileWidget {{
                background-color: {bg_color};
                border: {self.BORDER_WIDTH}px solid {border_color};
                border-radius: 4px;
            }}
            TileWidget:hover {{
                border-color: #1976D2;
            }}
        """)
    
    def paintEvent(self, event) -> None:
        """Custom paint to draw resize handle in edit mode.
        
        Args:
            event: Paint event.
        """
        super().paintEvent(event)
        
        if self.is_edit_mode:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw resize handle in bottom-right corner
            handle_rect = self._get_resize_handle_rect()
            
            # Fill
            painter.fillRect(handle_rect, QColor("#2196F3"))
            
            # Border
            pen = QPen(QColor("#1976D2"))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(handle_rect)
    
    def _get_resize_handle_rect(self) -> QRect:
        """Get the resize handle rectangle.
        
        Returns:
            QRect for the resize handle.
        """
        return QRect(
            self.width() - self.RESIZE_HANDLE_SIZE - 2,
            self.height() - self.RESIZE_HANDLE_SIZE - 2,
            self.RESIZE_HANDLE_SIZE,
            self.RESIZE_HANDLE_SIZE
        )
    
    def _is_in_resize_handle(self, pos: QPoint) -> bool:
        """Check if a position is within the resize handle.
        
        Args:
            pos: Position to check.
        
        Returns:
            True if position is in resize handle.
        """
        if not self.is_edit_mode:
            return False
        
        return self._get_resize_handle_rect().contains(pos)
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press for drag/resize.
        
        Args:
            event: Mouse event.
        """
        if not self.is_edit_mode:
            return
        
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_in_resize_handle(event.pos()):
                self.is_resizing = True
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.is_dragging = True
                self.drag_start_pos = event.globalPosition().toPoint()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for drag/resize.
        
        Args:
            event: Mouse event.
        """
        if not self.is_edit_mode:
            return
        
        # Update cursor based on hover
        if not self.is_dragging and not self.is_resizing:
            if self._is_in_resize_handle(event.pos()):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release to end drag/resize.
        
        Args:
            event: Mouse event.
        """
        if not self.is_edit_mode:
            return
        
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_dragging:
                # Calculate new grid position
                delta = event.globalPosition().toPoint() - self.drag_start_pos
                new_x = self.x() + delta.x()
                new_y = self.y() + delta.y()
                
                new_row = round(new_y / self.cell_size)
                new_col = round(new_x / self.cell_size)
                
                self.move_requested.emit(new_row, new_col)
            
            elif self.is_resizing:
                # Calculate new size based on mouse position
                new_width = max(1, round(event.pos().x() / self.cell_size))
                new_height = max(1, round(event.pos().y() / self.cell_size))
                
                self.resize_requested.emit(new_width, new_height)
            
            self.is_dragging = False
            self.is_resizing = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def keyPressEvent(self, event) -> None:
        """Handle keyboard input for moving/resizing.
        
        Args:
            event: Key event.
        """
        if not self.is_edit_mode:
            return
        
        key = event.key()
        modifiers = event.modifiers()
        
        # Arrow keys to move
        if modifiers == Qt.KeyboardModifier.NoModifier:
            if key == Qt.Key.Key_Up:
                self.move_requested.emit(self.tile.row - 1, self.tile.col)
            elif key == Qt.Key.Key_Down:
                self.move_requested.emit(self.tile.row + 1, self.tile.col)
            elif key == Qt.Key.Key_Left:
                self.move_requested.emit(self.tile.row, self.tile.col - 1)
            elif key == Qt.Key.Key_Right:
                self.move_requested.emit(self.tile.row, self.tile.col + 1)
        
        # Shift+Arrow to resize
        elif modifiers == Qt.KeyboardModifier.ShiftModifier:
            if key == Qt.Key.Key_Up:
                self.resize_requested.emit(self.tile.width, self.tile.height - 1)
            elif key == Qt.Key.Key_Down:
                self.resize_requested.emit(self.tile.width, self.tile.height + 1)
            elif key == Qt.Key.Key_Left:
                self.resize_requested.emit(self.tile.width - 1, self.tile.height)
            elif key == Qt.Key.Key_Right:
                self.resize_requested.emit(self.tile.width + 1, self.tile.height)
        
        # Delete key to remove
        elif key == Qt.Key.Key_Delete:
            self.remove_requested.emit()
    
    def contextMenuEvent(self, event) -> None:
        """Show context menu on right-click.
        
        Args:
            event: Context menu event.
        """
        if not self.is_edit_mode:
            return
        
        menu = QMenu(self)
        
        # Settings action
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        # Move to actions
        move_menu = menu.addMenu("Move to...")
        
        move_top_left = QAction("Top Left", self)
        move_top_left.triggered.connect(lambda: self.move_requested.emit(0, 0))
        move_menu.addAction(move_top_left)
        
        move_top_right = QAction("Top Right", self)
        move_top_right.triggered.connect(
            lambda: self.move_requested.emit(0, 8 - self.tile.width)
        )
        move_menu.addAction(move_top_right)
        
        move_bottom_left = QAction("Bottom Left", self)
        move_bottom_left.triggered.connect(
            lambda: self.move_requested.emit(8 - self.tile.height, 0)
        )
        move_menu.addAction(move_bottom_left)
        
        move_bottom_right = QAction("Bottom Right", self)
        move_bottom_right.triggered.connect(
            lambda: self.move_requested.emit(8 - self.tile.height, 8 - self.tile.width)
        )
        move_menu.addAction(move_bottom_right)
        
        menu.addSeparator()
        
        # Remove action
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.remove_requested.emit)
        menu.addAction(remove_action)
        
        menu.exec(event.globalPos())