"""Clock widget worker process.

This script runs the clock widget in a separate process.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from plugins_host.worker import PluginWorker
from examples.clock_widget.clock_plugin import ClockPlugin
from core.plugin_api import WidgetPlugin, PluginMetadata


class ClockWorker(PluginWorker):
    """Worker for clock widget."""
    
    def _create_plugin_instance(self, plugin_id: str, settings: dict) -> WidgetPlugin:
        """Create clock plugin instance."""
        # Create minimal metadata
        metadata = PluginMetadata(
            plugin_id=plugin_id,
            name="Clock",
            version="1.0.0",
            description="Digital clock widget",
            author="WidgetBoard",
            module_path="examples.clock_widget",
            class_name="ClockPlugin"
        )
        
        # Create plugin instance
        plugin = ClockPlugin(
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
    
    worker = ClockWorker(endpoint, instance_id)
    worker.run()
