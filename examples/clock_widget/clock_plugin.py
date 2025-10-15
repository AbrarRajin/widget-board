"""Clock widget plugin implementation."""

from datetime import datetime
from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from core.plugin_api import PluginBase


class ClockPlugin(PluginBase):
    """A simple clock widget that displays the current time."""
    
    def __init__(self) -> None:
        """Initialize the clock plugin."""
        super().__init__()
        self._timer: QTimer | None = None
        self._time_label: QLabel | None = None
        self._date_label: QLabel | None = None
        self._widget: QWidget | None = None
    
    def get_widget(self) -> QWidget:
        """Create and return the clock widget.
        
        Returns:
            QWidget with clock display.
        """
        if self._widget is not None:
            return self._widget
        
        # Create widget
        self._widget = QWidget()
        layout = QVBoxLayout(self._widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Time label
        self._time_label = QLabel("--:--:--")
        time_font = QFont()
        time_font.setPointSize(self.settings.get("font_size", 24))
        time_font.setBold(True)
        self._time_label.setFont(time_font)
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._time_label)
        
        # Date label (optional)
        if self.settings.get("show_date", True):
            self._date_label = QLabel("")
            date_font = QFont()
            date_font.setPointSize(12)
            self._date_label.setFont(date_font)
            self._date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self._date_label)
        
        # Apply colors
        self._apply_colors()
        
        # Update immediately
        self._update_display()
        
        return self._widget
    
    def start(self) -> None:
        """Start the clock timer."""
        super().start()
        
        # Create timer for updates
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_display)
        
        # Update every second if showing seconds, otherwise every minute
        interval = 1000 if self.settings.get("show_seconds", True) else 60000
        self._timer.start(interval)
    
    def stop(self) -> None:
        """Stop the clock timer."""
        if self._timer:
            self._timer.stop()
        super().stop()
    
    def update(self, settings: Dict[str, Any]) -> None:
        """Update clock with new settings.
        
        Args:
            settings: New settings dictionary.
        """
        super().update(settings)
        
        # Restart timer if interval changed
        if self._timer:
            interval = 1000 if settings.get("show_seconds", True) else 60000
            self._timer.setInterval(interval)
        
        # Update font size
        if self._time_label:
            font = self._time_label.font()
            font.setPointSize(settings.get("font_size", 24))
            self._time_label.setFont(font)
        
        # Show/hide date
        if self._date_label:
            self._date_label.setVisible(settings.get("show_date", True))
        
        # Update colors
        self._apply_colors()
        
        # Refresh display
        self._update_display()
    
    def dispose(self) -> None:
        """Clean up clock resources."""
        if self._timer:
            self._timer.stop()
            self._timer = None
        super().dispose()
    
    def _update_display(self) -> None:
        """Update the time and date display."""
        if not self._time_label:
            return
        
        now = datetime.now()
        
        # Format time
        use_24h = self.settings.get("format_24h", False)
        show_seconds = self.settings.get("show_seconds", True)
        
        if use_24h:
            if show_seconds:
                time_str = now.strftime("%H:%M:%S")
            else:
                time_str = now.strftime("%H:%M")
        else:
            if show_seconds:
                time_str = now.strftime("%I:%M:%S %p")
            else:
                time_str = now.strftime("%I:%M %p")
        
        self._time_label.setText(time_str)
        
        # Format date
        if self._date_label and self.settings.get("show_date", True):
            date_format = self.settings.get("date_format", "MM/DD/YYYY")
            
            if date_format == "MM/DD/YYYY":
                date_str = now.strftime("%m/%d/%Y")
            elif date_format == "DD/MM/YYYY":
                date_str = now.strftime("%d/%m/%Y")
            else:  # YYYY-MM-DD
                date_str = now.strftime("%Y-%m-%d")
            
            # Add day of week
            day_of_week = now.strftime("%A")
            self._date_label.setText(f"{day_of_week}, {date_str}")
    
    def _apply_colors(self) -> None:
        """Apply text and background colors from settings."""
        if not self._widget:
            return
        
        text_color = self.settings.get("text_color", "#000000")
        bg_color = self.settings.get("background_color", "#FFFFFF")
        
        style = f"""
            QWidget {{
                background-color: {bg_color};
            }}
            QLabel {{
                color: {text_color};
            }}
        """
        self._widget.setStyleSheet(style)
