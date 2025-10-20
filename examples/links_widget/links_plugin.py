"""Links widget plugin implementation."""

from typing import Dict, Any, List
from core.plugin_api import WidgetPlugin, PluginMetadata  # Changed from PluginBase


class LinksPlugin(WidgetPlugin):  # Changed from PluginBase
    """A widget that displays quick access links."""
    
    def __init__(
        self,
        instance_id: str,
        plugin_id: str,
        metadata: PluginMetadata,
        settings: Dict[str, Any]
    ):
        """Initialize the links plugin."""
        super().__init__(instance_id, plugin_id, metadata, settings)
    
    def init(self) -> None:
        """Initialize the plugin."""
        super().init()
    
    def start(self) -> None:
        """Start the plugin lifecycle."""
        super().start()
    
    def update(self, delta_time: float) -> None:
        """Update plugin state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        # Links are static, nothing to update
        pass
    
    def get_render_data(self) -> Dict[str, Any]:
        """Get render data for this plugin.
        
        Returns:
            Dictionary containing HTML to display
        """
        # Get links from settings
        links = self.settings.get("links", [
            {"title": "Google", "url": "https://www.google.com"},
            {"title": "GitHub", "url": "https://github.com"},
            {"title": "Stack Overflow", "url": "https://stackoverflow.com"}
        ])
        
        # Get theme settings
        bg_color = self.settings.get("background_color", "#1976D2")
        text_color = self.settings.get("text_color", "#FFFFFF")
        
        # Build HTML for links
        links_html = ""
        for link in links:
            title = link.get("title", "Link")
            url = link.get("url", "#")
            links_html += f"""
            <a href="{url}" target="_blank" style="
                display: block;
                padding: 12px 16px;
                margin: 8px 0;
                background: rgba(255, 255, 255, 0.1);
                color: {text_color};
                text-decoration: none;
                border-radius: 6px;
                font-weight: 500;
                transition: all 0.2s;
                border: 1px solid rgba(255, 255, 255, 0.2);
            " onmouseover="this.style.background='rgba(255, 255, 255, 0.2)'" 
               onmouseout="this.style.background='rgba(255, 255, 255, 0.1)'">
                {title}
            </a>
            """
        
        html = f"""
        <div style="
            display: flex;
            flex-direction: column;
            height: 100%;
            background: linear-gradient(135deg, {bg_color} 0%, {bg_color}CC 100%);
            color: {text_color};
            font-family: 'Segoe UI', Arial, sans-serif;
            border-radius: 8px;
            padding: 16px;
        ">
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 12px;">
                Quick Links
            </div>
            <div style="flex: 1; overflow-y: auto;">
                {links_html}
            </div>
        </div>
        """
        
        return {
            "html": html,
            "needs_update": False  # Links are static
        }
    
    def on_settings_changed(self, new_settings: Dict[str, Any]) -> None:
        """Handle settings change.
        
        Args:
            new_settings: New settings dictionary
        """
        super().on_settings_changed(new_settings)
        # Links updated, trigger re-render
    
    def dispose(self) -> None:
        """Dispose of the plugin and clean up resources."""
        super().dispose()