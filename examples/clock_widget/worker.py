"""Worker process for clock widget plugin."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from plugins_host.worker import PluginWorker
from examples.clock_widget.clock_plugin import ClockPlugin  # Fixed import path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ClockWorker(PluginWorker):
    """Clock widget worker process."""
    
    def _create_plugin_instance(
        self,
        plugin_id: str,
        settings: Dict[str, Any]
    ) -> ClockPlugin:
        """Create the clock plugin instance."""
        plugin = ClockPlugin(
            instance_id=self.instance_id,
            settings=settings
        )
        
        logger.info(f"Clock plugin instance created: {self.instance_id}")
        return plugin
    
    def _get_plugin_data(self, reason: str) -> Dict[str, Any]:
        """Get data from the clock plugin."""
        if not self.plugin:
            raise RuntimeError("Plugin not initialized")
        
        # Get data from plugin
        data = self.plugin.get_data(reason)
        
        # Wrap in expected format
        return {
            "status": "ok",
            "data": data,
            "ttl_ms": 1000 if self.plugin.show_seconds else 60000
        }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: worker.py <endpoint> <instance_id>")
        sys.exit(1)
    
    endpoint = sys.argv[1]
    instance_id = sys.argv[2]
    
    worker = ClockWorker(endpoint, instance_id)
    worker.run()