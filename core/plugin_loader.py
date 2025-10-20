"""Plugin loader and registry.

Discovers, loads, and manages plugin instances.
Supports both in-process and out-of-process (IPC) plugins.
"""

import logging
import importlib
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Type
from core.plugin_api import WidgetPlugin, PluginMetadata, ExecutionMode
from core.manifest_parser import ManifestParser
from core.plugin_proxy import PluginProxy
from plugins_host.supervisor import PluginSupervisor

logger = logging.getLogger(__name__)


class PluginLoader:
    """Discovers and loads plugins from the examples directory."""
    
    def __init__(self, plugins_dir: str = "examples"):
        """Initialize the plugin loader.
        
        Args:
            plugins_dir: Directory to search for plugins
        """
        self.plugins_dir = Path(plugins_dir)
        self._metadata: Dict[str, PluginMetadata] = {}
        self._classes: Dict[str, Type[WidgetPlugin]] = {}
        self._instances: Dict[str, WidgetPlugin] = {}  # instance_id -> plugin
        self._supervisor = PluginSupervisor(base_port=5555)
    
    def discover_plugins(self) -> List[PluginMetadata]:
        """Discover all plugins in the plugins directory.
        
        Searches for directories containing manifest.json files.
        
        Returns:
            List of discovered plugin metadata
        """
        discovered = []
        
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return discovered
        
        # Search for manifest.json files
        for manifest_path in self.plugins_dir.rglob("manifest.json"):
            metadata = ManifestParser.parse(manifest_path)
            if metadata:
                self._metadata[metadata.plugin_id] = metadata
                discovered.append(metadata)
        
        logger.info(f"Discovered {len(discovered)} plugins")
        for meta in discovered:
            logger.info(f"  - {meta.name} ({meta.execution_mode.value})")
        
        return discovered
    
    def load_plugin_class(self, plugin_id: str) -> Optional[Type[WidgetPlugin]]:
        """Load a plugin class by its ID.
        
        Args:
            plugin_id: The plugin's unique identifier
            
        Returns:
            Plugin class if successful, None otherwise
        """
        # Return cached class if already loaded
        if plugin_id in self._classes:
            return self._classes[plugin_id]
        
        # Get metadata
        if plugin_id not in self._metadata:
            logger.error(f"Plugin not found: {plugin_id}")
            return None
        
        metadata = self._metadata[plugin_id]
        
        # For out-of-process plugins, we don't need to load the class
        if metadata.execution_mode == ExecutionMode.OUT_OF_PROCESS:
            logger.info(f"Plugin {plugin_id} runs out-of-process, no class loading needed")
            return None
        
        # Load in-process plugin class
        try:
            module = importlib.import_module(metadata.module_path)
            plugin_class = getattr(module, metadata.class_name)
            
            if not issubclass(plugin_class, WidgetPlugin):
                logger.error(f"Plugin class {metadata.class_name} must inherit from WidgetPlugin")
                return None
            
            self._classes[plugin_id] = plugin_class
            logger.info(f"Loaded plugin class: {plugin_id}")
            return plugin_class
            
        except ImportError as e:
            logger.error(f"Failed to import plugin module {metadata.module_path}: {e}")
            return None
        except AttributeError as e:
            logger.error(f"Plugin class {metadata.class_name} not found in {metadata.module_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading plugin class {plugin_id}: {e}", exc_info=True)
            return None
    
    def create_instance(
        self,
        plugin_id: str,
        instance_id: Optional[str] = None,
        settings: Optional[Dict] = None
    ) -> Optional[WidgetPlugin]:
        """Create a new plugin instance.
        
        Args:
            plugin_id: Plugin type identifier
            instance_id: Unique instance ID (generated if not provided)
            settings: Initial settings (uses defaults if not provided)
            
        Returns:
            Plugin instance if successful, None otherwise
        """
        # Get metadata
        if plugin_id not in self._metadata:
            logger.error(f"Plugin not found: {plugin_id}")
            return None
        
        metadata = self._metadata[plugin_id]
        
        # Generate instance ID if not provided
        if instance_id is None:
            instance_id = f"{plugin_id}_{uuid.uuid4().hex[:8]}"
        
        # Use default settings if not provided
        if settings is None:
            settings = {}
        
        # Create instance based on execution mode
        try:
            if metadata.execution_mode == ExecutionMode.IN_PROCESS:
                # In-process plugin
                plugin_class = self.load_plugin_class(plugin_id)
                if plugin_class is None:
                    return None
                
                plugin = plugin_class(instance_id, plugin_id, metadata, settings)
                plugin.init()
                
                logger.info(f"Created in-process plugin instance: {instance_id} ({plugin_id})")
                
            else:
                # Out-of-process plugin (create proxy)
                if not metadata.worker_script:
                    logger.error(f"Worker script not specified for out-of-process plugin: {plugin_id}")
                    return None
                
                plugin = PluginProxy(
                    supervisor=self._supervisor,
                    instance_id=instance_id,
                    plugin_id=plugin_id,
                    metadata=metadata,
                    worker_script=Path(metadata.worker_script),
                    settings=settings
                )
                plugin.init()
                
                logger.info(f"Created out-of-process plugin instance: {instance_id} ({plugin_id})")
            
            # Store instance
            self._instances[instance_id] = plugin
            return plugin
            
        except Exception as e:
            logger.error(f"Error creating plugin instance: {e}", exc_info=True)
            return None
    
    def get_instance(self, instance_id: str) -> Optional[WidgetPlugin]:
        """Get a plugin instance by ID.
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            Plugin instance if found, None otherwise
        """
        return self._instances.get(instance_id)
    
    def start_instance(self, instance_id: str) -> bool:
        """Start a plugin instance.
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            True if started successfully
        """
        plugin = self.get_instance(instance_id)
        if plugin is None:
            logger.warning(f"Plugin instance not found: {instance_id}")
            return False
        
        try:
            plugin.start()
            return True
        except Exception as e:
            logger.error(f"Error starting plugin {instance_id}: {e}", exc_info=True)
            return False
    
    def stop_instance(self, instance_id: str) -> bool:
        """Stop a plugin instance.
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            True if stopped successfully
        """
        plugin = self.get_instance(instance_id)
        if plugin is None:
            return False
        
        try:
            plugin.stop()
            return True
        except Exception as e:
            logger.error(f"Error stopping plugin {instance_id}: {e}", exc_info=True)
            return False
    
    def update_instance(self, instance_id: str, delta_time: float) -> bool:
        """Update a plugin instance.
        
        Args:
            instance_id: Instance identifier
            delta_time: Time since last update
            
        Returns:
            True if updated successfully
        """
        plugin = self.get_instance(instance_id)
        if plugin is None:
            return False
        
        try:
            plugin.update(delta_time)
            return True
        except Exception as e:
            logger.error(f"Error updating plugin {instance_id}: {e}", exc_info=True)
            return False
    
    def dispose_instance(self, instance_id: str) -> None:
        """Dispose of a plugin instance.
        
        Args:
            instance_id: Instance identifier
        """
        plugin = self._instances.pop(instance_id, None)
        if plugin is None:
            return
        
        try:
            plugin.dispose()
            logger.info(f"Disposed plugin instance: {instance_id}")
        except Exception as e:
            logger.error(f"Error disposing plugin {instance_id}: {e}", exc_info=True)
    
    def get_metadata(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by ID.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Plugin metadata if found, None otherwise
        """
        return self._metadata.get(plugin_id)
    
    def get_all_metadata(self) -> List[PluginMetadata]:
        """Get metadata for all discovered plugins.
        
        Returns:
            List of plugin metadata
        """
        return list(self._metadata.values())
    
    def shutdown(self) -> None:
        """Shutdown all plugins and clean up resources."""
        logger.info("Shutting down plugin loader")
        
        # Dispose all instances
        for instance_id in list(self._instances.keys()):
            self.dispose_instance(instance_id)
        
        # Shutdown supervisor (terminates all worker processes)
        self._supervisor.shutdown_all()