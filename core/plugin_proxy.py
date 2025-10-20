"""Plugin proxy for out-of-process plugins.

This module provides a proxy that implements the WidgetPlugin interface
but delegates all operations to an out-of-process plugin via IPC.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from core.plugin_api import WidgetPlugin, PluginMetadata
from plugins_host.supervisor import PluginSupervisor

logger = logging.getLogger(__name__)


class PluginProxy(WidgetPlugin):
    """Proxy for out-of-process plugins using IPC.
    
    This class implements the WidgetPlugin interface but delegates
    all operations to a plugin running in a separate process.
    """
    
    def __init__(
        self,
        supervisor: PluginSupervisor,
        instance_id: str,
        plugin_id: str,
        metadata: PluginMetadata,
        worker_script: Path,
        settings: Dict[str, Any]
    ):
        """Initialize plugin proxy.
        
        Args:
            supervisor: Plugin supervisor managing the process
            instance_id: Unique instance identifier
            plugin_id: Plugin type identifier
            metadata: Plugin metadata
            worker_script: Path to worker script
            settings: Initial settings
        """
        super().__init__(instance_id, plugin_id, metadata, settings)
        self.supervisor = supervisor
        self.worker_script = worker_script
        self._initialized = False
    
    def init(self) -> None:
        """Initialize the plugin (spawn worker process)."""
        if self._initialized:
            logger.warning(f"Plugin proxy {self.instance_id} already initialized")
            return
        
        logger.info(f"Initializing plugin proxy: {self.plugin_id} (instance: {self.instance_id})")
        
        # Spawn worker process
        success = self.supervisor.spawn_plugin(
            instance_id=self.instance_id,
            plugin_id=self.plugin_id,
            worker_script=self.worker_script,
            settings=self.settings
        )
        
        if not success:
            raise RuntimeError(f"Failed to spawn plugin worker: {self.plugin_id}")
        
        self._initialized = True
        logger.info(f"Plugin proxy initialized: {self.instance_id}")
    
    def start(self) -> None:
        """Start the plugin lifecycle (already handled in spawn_plugin)."""
        if not self._initialized:
            raise RuntimeError("Plugin proxy not initialized")
        
        # START message is already sent during spawn_plugin
        logger.debug(f"Plugin proxy started: {self.instance_id}")
    
    def update(self, delta_time: float) -> None:
        """Update plugin state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        if not self._initialized:
            return
        
        # Send update message to worker
        self.supervisor.send_update(self.instance_id, delta_time)
    
    def get_render_data(self) -> Dict[str, Any]:
        """Get render data from plugin.
        
        Returns:
            Dictionary containing render data
        """
        if not self._initialized:
            return {"html": "<div>Plugin not initialized</div>"}
        
        # Request render from worker (using fixed size for now)
        render_data = self.supervisor.request_render(
            instance_id=self.instance_id,
            width=400,
            height=300
        )
        
        if render_data is None:
            logger.warning(f"Failed to get render data from {self.instance_id}")
            return {"html": "<div>Render error</div>"}
        
        return render_data.get("render_data", {})
    
    def on_settings_changed(self, new_settings: Dict[str, Any]) -> None:
        """Handle settings change.
        
        Args:
            new_settings: New settings dictionary
        """
        if not self._initialized:
            return
        
        self.settings = new_settings
        
        # Send settings update to worker
        success = self.supervisor.update_settings(self.instance_id, new_settings)
        
        if not success:
            logger.warning(f"Failed to update settings for {self.instance_id}")
    
    def dispose(self) -> None:
        """Dispose plugin resources (terminate worker process)."""
        if not self._initialized:
            return
        
        logger.info(f"Disposing plugin proxy: {self.instance_id}")
        
        # Terminate worker process
        self.supervisor.terminate_plugin(self.instance_id)
        
        self._initialized = False
