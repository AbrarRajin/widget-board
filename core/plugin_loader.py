"""Plugin loader and registry.

Discovers, loads, and manages plugin instances.
"""

import logging
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Type
from core.plugin_api import PluginBase, PluginMetadata, PluginState
from core.manifest_parser import ManifestParser


logger = logging.getLogger(__name__)


class PluginLoader:
    """Discovers and loads plugins from the examples directory."""
    
    def __init__(self, plugins_dir: str = "examples") -> None:
        """Initialize the plugin loader.
        
        Args:
            plugins_dir: Directory to search for plugins.
        """
        self.plugins_dir = Path(plugins_dir)
        self._metadata: Dict[str, PluginMetadata] = {}
        self._classes: Dict[str, Type[PluginBase]] = {}
        self._instances: Dict[str, PluginBase] = {}  # instance_id -> plugin
    
    def discover_plugins(self) -> List[PluginMetadata]:
        """Discover all plugins in the plugins directory.
        
        Searches for directories containing manifest.json files.
        
        Returns:
            List of discovered plugin metadata.
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
        return discovered
    
    def load_plugin_class(self, plugin_id: str) -> Optional[Type[PluginBase]]:
        """Load a plugin class by its ID.
        
        Args:
            plugin_id: The plugin's unique identifier.
            
        Returns:
            Plugin class if successful, None otherwise.
        """
        if plugin_id in self._classes:
            return self._classes[plugin_id]
        
        metadata = self._metadata.get(plugin_id)
        if not metadata:
            logger.error(f"Plugin not found: {plugin_id}")
            return None
        
        try:
            # Import the module
            module = importlib.import_module(metadata.module_path)
            
            # Get the class
            plugin_class = getattr(module, metadata.class_name)
            
            # Verify it's a PluginBase subclass
            if not issubclass(plugin_class, PluginBase):
                logger.error(
                    f"Plugin class {metadata.class_name} does not inherit from PluginBase"
                )
                return None
            
            self._classes[plugin_id] = plugin_class
            logger.info(f"Loaded plugin class: {metadata.name}")
            return plugin_class
            
        except ImportError as e:
            logger.error(f"Failed to import plugin {plugin_id}: {e}")
            return None
        except AttributeError as e:
            logger.error(
                f"Plugin class {metadata.class_name} not found in module {metadata.module_path}: {e}"
            )
            return None
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_id}: {e}")
            return None
    
    def create_instance(
        self,
        plugin_id: str,
        instance_id: str,
        settings: Dict
    ) -> Optional[PluginBase]:
        """Create a new plugin instance.
        
        Args:
            plugin_id: The plugin's unique identifier.
            instance_id: Unique ID for this instance.
            settings: Settings dictionary for the instance.
            
        Returns:
            Plugin instance if successful, None otherwise.
        """
        # Check if instance already exists
        if instance_id in self._instances:
            logger.warning(f"Plugin instance already exists: {instance_id}")
            return self._instances[instance_id]
        
        # Load the plugin class
        plugin_class = self.load_plugin_class(plugin_id)
        if not plugin_class:
            return None
        
        try:
            # Create instance
            instance = plugin_class()
            
            # Initialize with instance ID and settings
            instance.initialize(instance_id, settings)
            
            # Register instance
            self._instances[instance_id] = instance
            
            logger.info(f"Created plugin instance: {instance_id} ({plugin_id})")
            return instance
            
        except Exception as e:
            logger.error(f"Error creating plugin instance {instance_id}: {e}")
            return None
    
    def get_instance(self, instance_id: str) -> Optional[PluginBase]:
        """Get an existing plugin instance.
        
        Args:
            instance_id: The instance ID.
            
        Returns:
            Plugin instance if found, None otherwise.
        """
        return self._instances.get(instance_id)
    
    def destroy_instance(self, instance_id: str) -> bool:
        """Destroy a plugin instance.
        
        Args:
            instance_id: The instance ID to destroy.
            
        Returns:
            True if destroyed successfully, False otherwise.
        """
        instance = self._instances.get(instance_id)
        if not instance:
            logger.warning(f"Plugin instance not found: {instance_id}")
            return False
        
        try:
            # Dispose of the instance
            if instance.state != PluginState.DISPOSED:
                instance.dispose()
            
            # Remove from registry
            del self._instances[instance_id]
            
            logger.info(f"Destroyed plugin instance: {instance_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error destroying plugin instance {instance_id}: {e}")
            return False
    
    def get_metadata(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get metadata for a plugin.
        
        Args:
            plugin_id: The plugin's unique identifier.
            
        Returns:
            Plugin metadata if found, None otherwise.
        """
        return self._metadata.get(plugin_id)
    
    def get_all_metadata(self) -> List[PluginMetadata]:
        """Get metadata for all discovered plugins.
        
        Returns:
            List of all plugin metadata.
        """
        return list(self._metadata.values())
    
    def start_instance(self, instance_id: str) -> bool:
        """Start a plugin instance.
        
        Args:
            instance_id: The instance ID.
            
        Returns:
            True if started successfully, False otherwise.
        """
        instance = self.get_instance(instance_id)
        if not instance:
            return False
        
        try:
            instance.start()
            return True
        except Exception as e:
            logger.error(f"Error starting instance {instance_id}: {e}")
            instance.handle_error(str(e))
            return False
    
    def stop_instance(self, instance_id: str) -> bool:
        """Stop a plugin instance.
        
        Args:
            instance_id: The instance ID.
            
        Returns:
            True if stopped successfully, False otherwise.
        """
        instance = self.get_instance(instance_id)
        if not instance:
            return False
        
        try:
            instance.stop()
            return True
        except Exception as e:
            logger.error(f"Error stopping instance {instance_id}: {e}")
            instance.handle_error(str(e))
            return False
    
    def update_instance(self, instance_id: str, settings: Dict) -> bool:
        """Update a plugin instance with new settings.
        
        Args:
            instance_id: The instance ID.
            settings: New settings dictionary.
            
        Returns:
            True if updated successfully, False otherwise.
        """
        instance = self.get_instance(instance_id)
        if not instance:
            return False
        
        try:
            instance.update(settings)
            return True
        except Exception as e:
            logger.error(f"Error updating instance {instance_id}: {e}")
            instance.handle_error(str(e))
            return False
