"""Links widget worker process.

This script runs the links widget in a separate process.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from plugins_host.worker import PluginWorker
from examples.links_widget.links_plugin import LinksPlugin
from core.plugin_api import WidgetPlugin, PluginMetadata


class LinksWorker(PluginWorker):
    """Worker for links widget."""
    
    def _create_plugin_instance(self, plugin_id: str, settings: dict) -> WidgetPlugin:
        """Create links plugin instance."""
        # Create minimal metadata
        metadata = PluginMetadata(
            plugin_id=plugin_id,
            name="Quick Links",
            version="1.0.0",
            description="Quick access links widget",
            author="WidgetBoard",
            module_path="examples.links_widget",
            class_name="LinksPlugin"
        )
        
        # Create plugin instance
        plugin = LinksPlugin(
            instance_id=self.instance_id,
            plugin_id=plugin_id,
            metadata=metadata,
            settings=settings
        )
        
        return plugin


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python worker.py <endpoint> <instance_id>")
        sys.exit(1)
    
    endpoint = sys.argv[1]
    instance_id = sys.argv[2]
    
    worker = LinksWorker(endpoint, instance_id)
    worker.run()
