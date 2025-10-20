"""Links plugin implementation."""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class LinksPlugin:
    """Quick links widget."""
    
    def __init__(
        self,
        instance_id: str = None,
        settings: Dict[str, Any] = None,
        plugin_id: str = None,  # Accept but ignore
        **kwargs
    ):
        """Initialize links plugin."""
        self.instance_id = instance_id or "links_unknown"
        self.settings = settings or {}
        
        # Default links
        self.links = self.settings.get("links", [
            {"title": "GitHub", "url": "https://github.com", "category": "Development"},
            {"title": "Stack Overflow", "url": "https://stackoverflow.com", "category": "Development"},
            {"title": "Gmail", "url": "https://gmail.com", "category": "Productivity"},
        ])
        
        logger.info(f"LinksPlugin initialized: {self.instance_id}")
    
    def get_data(self, reason: str = "update") -> Dict[str, Any]:
        """Get links data."""
        items = []
        for link in self.links:
            items.append({
                "text": link["title"],
                "secondary": f"{link.get('category', 'Link')} • {link['url']}"
            })
        
        return {
            "layout": "list",
            "content": {
                "items": items,
                "max_items": 10
            }
        }
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update plugin settings."""
        self.settings.update(settings)
        self.links = self.settings.get("links", self.links)
        logger.info(f"Settings updated for {self.instance_id}")
    
    def dispose(self) -> None:
        """Cleanup resources."""
        logger.info(f"LinksPlugin disposed: {self.instance_id}")