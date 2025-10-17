"""Clock widget plugin implementation."""

from datetime import datetime
from typing import Dict, Any
from PySide6.QtCore import QTimer
from core.plugin_api import WidgetPlugin, PluginMetadata  # Changed from PluginBase


class ClockPlugin(WidgetPlugin):  # Changed from PluginBase
    """A simple clock widget that displays the current time."""
    
    def __init__(
        self,
        instance_id: str,
        plugin_id: str,
        metadata: PluginMetadata,
        settings: Dict[str, Any]
    ):
        """Initialize the clock plugin."""
        super().__init__(instance_id, plugin_id, metadata, settings)
        self._timer = None
        self._current_time = ""
    
    def init(self) -> None:
        """Initialize the plugin."""
        super().init()
        self._update_time()
    
    def start(self) -> None:
        """Start the clock timer."""
        super().start()
        
        # Create timer for updates
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer)
        
        # Update every second
        self._timer.start(1000)
    
    def stop(self) -> None:
        """Stop the clock timer."""
        if self._timer:
            self._timer.stop()
        super().stop()
    
    def update(self, delta_time: float) -> None:
        """Update plugin state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        # Timer handles updates, nothing to do here
        pass
    
    def _on_timer(self) -> None:
        """Handle timer tick."""
        self._update_time()
        self.render_updated.emit()
    
    def _update_time(self) -> None:
        """Update the current time string."""
        now = datetime.now()
        
        # Get format settings
        use_24h = self.settings.get("use_24h_format", False)
        show_seconds = self.settings.get("show_seconds", True)
        show_date = self.settings.get("show_date", True)
        
        # Format time
        if use_24h:
            time_format = "%H:%M:%S" if show_seconds else "%H:%M"
        else:
            time_format = "%I:%M:%S %p" if show_seconds else "%I:%M %p"
        
        time_str = now.strftime(time_format)
        
        # Add date if enabled
        if show_date:
            date_str = now.strftime("%A, %B %d, %Y")
            self._current_time = f"{time_str}<br><span style='font-size: 14px;'>{date_str}</span>"
        else:
            self._current_time = time_str
    
    def get_render_data(self) -> Dict[str, Any]:
        """Get render data for this plugin.
        
        Returns:
            Dictionary containing HTML to display
        """
        # Get theme settings
        bg_color = self.settings.get("background_color", "#2196F3")
        text_color = self.settings.get("text_color", "#FFFFFF")
        font_size = self.settings.get("font_size", 32)
        
        html = f"""
        <div style="
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100%;
            background: linear-gradient(135deg, {bg_color} 0%, {bg_color}CC 100%);
            color: {text_color};
            font-family: 'Segoe UI', Arial, sans-serif;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: {font_size}px; font-weight: bold;">
                {self._current_time}
            </div>
        </div>
        """
        
        return {
            "html": html,
            "needs_update": True  # Clock needs continuous updates
        }
    
    def on_settings_changed(self, new_settings: Dict[str, Any]) -> None:
        """Handle settings change.
        
        Args:
            new_settings: New settings dictionary
        """
        super().on_settings_changed(new_settings)
        
        # Update timer interval if show_seconds changed
        if self._timer and self._timer.isActive():
            show_seconds = new_settings.get("show_seconds", True)
            interval = 1000 if show_seconds else 60000
            self._timer.setInterval(interval)
        
        # Update display
        self._update_time()
    
    def dispose(self) -> None:
        """Dispose of the plugin and clean up resources."""
        if self._timer:
            self._timer.stop()
            self._timer = None
        super().dispose()