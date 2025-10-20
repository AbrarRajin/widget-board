"""Status indicator widget for tile state visualization."""
from typing import Optional
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor, QPainter, QPainterPath
from enum import Enum


class TileStatus(Enum):
    """Possible tile states."""
    OK = "ok"
    UPDATING = "updating"
    ERROR = "error"
    STARTING = "starting"
    SUSPENDED = "suspended"


class StatusIndicator(QWidget):
    """Visual status pill showing tile state with color and animation."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._status = TileStatus.OK
        self._message = ""
        self._opacity = 1.0
        
        # Setup UI
        self.setFixedHeight(20)
        self.setMinimumWidth(60)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(4)
        
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)
        
        # Pulse animation for updating state
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse)
        self._pulse_direction = 1
        
        self._update_appearance()
    
    def set_status(self, status: TileStatus, message: str = "") -> None:
        """Update the status indicator."""
        self._status = status
        self._message = message
        self._update_appearance()
        
        # Start/stop pulse for updating state
        if status == TileStatus.UPDATING:
            if not self._pulse_timer.isActive():
                self._pulse_timer.start(50)
        else:
            self._pulse_timer.stop()
            self._opacity = 1.0
    
    def _pulse(self) -> None:
        """Animate opacity for pulsing effect."""
        self._opacity += 0.05 * self._pulse_direction
        if self._opacity >= 1.0:
            self._opacity = 1.0
            self._pulse_direction = -1
        elif self._opacity <= 0.4:
            self._opacity = 0.4
            self._pulse_direction = 1
        self.update()
    
    def _update_appearance(self) -> None:
        """Update colors and text based on status."""
        status_config = {
            TileStatus.OK: ("✓", "#4CAF50", "#FFFFFF"),
            TileStatus.UPDATING: ("⟳", "#2196F3", "#FFFFFF"),
            TileStatus.ERROR: ("✗", "#F44336", "#FFFFFF"),
            TileStatus.STARTING: ("◐", "#FF9800", "#FFFFFF"),
            TileStatus.SUSPENDED: ("❙❙", "#9E9E9E", "#FFFFFF"),
        }
        
        symbol, bg_color, fg_color = status_config[self._status]
        text = f"{symbol} {self._status.value.title()}"
        if self._message:
            text = f"{symbol} {self._message}"
        
        self._label.setText(text)
        self._bg_color = QColor(bg_color)
        self._fg_color = QColor(fg_color)
        
        self._label.setStyleSheet(f"color: {fg_color}; font-size: 11px; font-weight: 500;")
        self.update()
    
    def paintEvent(self, event) -> None:
        """Custom paint for rounded pill background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Apply opacity
        bg = QColor(self._bg_color)
        bg.setAlphaF(self._opacity)
        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw rounded rectangle
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(0, 0, 0, 0), 10, 10)
        painter.drawPath(path)