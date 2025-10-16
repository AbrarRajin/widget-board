"""Plugin API and base classes.

This module defines the contract between the host application and plugins.
"""

from typing import Any, Dict, Optional
from enum import Enum
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject, Signal


class PluginState(Enum):
    """Plugin lifecycle states."""
    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    STARTED = "started"
    STOPPED = "stopped"
    DISPOSED = "disposed"
    ERROR = "error"


class PluginBase(QObject):
    """Base class for all plugins.
    
    Plugins must inherit from this class and implement the required methods.
    The host application manages the plugin lifecycle through these methods.
    
    Lifecycle:
        1. __init__() - Plugin is instantiated
        2. initialize() - Plugin receives its instance ID and initial settings
        3. start() - Plugin should begin operation (timers, subscriptions, etc.)
        4. update() - Called when settings or data changes
        5. stop() - Plugin should pause operation (optional, for suspend/resume)
        6. dispose() - Plugin should clean up resources before destruction
    
    Signals:
        data_changed: Emitted when plugin's display data changes
        error_occurred: Emitted when an error occurs in the plugin
        settings_changed: Emitted when plugin wants to update its settings
    """
    
    # Signals
    data_changed = Signal(dict)  # Emitted when display data changes
    error_occurred = Signal(str)  # Emitted on errors
    settings_changed = Signal(dict)  # Request settings update
    
    def __init__(self) -> None:
        """Initialize the plugin.
        
        This is called when the plugin class is first instantiated.
        Don't do heavy initialization here - use initialize() instead.
        """
        super().__init__()
        self._state = PluginState.UNINITIALIZED
        self._instance_id: Optional[str] = None
        self._settings: Dict[str, Any] = {}
    
    @property
    def state(self) -> PluginState:
        """Get current plugin state."""
        return self._state
    
    @property
    def instance_id(self) -> Optional[str]:
        """Get the unique instance ID for this plugin instance."""
        return self._instance_id
    
    @property
    def settings(self) -> Dict[str, Any]:
        """Get current plugin settings."""
        return self._settings.copy()
    
    def get_widget(self) -> QWidget:
        """Get the Qt widget to display in the tile.
        
        This method MUST be implemented by subclasses.
        
        This method is called once when the tile is created. The returned
        widget will be placed inside the tile and should update itself
        when data changes.
        
        Returns:
            QWidget: The widget to display in the tile.
        
        Raises:
            NotImplementedError: If the subclass doesn't implement this method.
        """
        raise NotImplementedError("Plugins must implement get_widget()")
    
    def initialize(self, instance_id: str, settings: Dict[str, Any]) -> None:
        """Initialize the plugin with instance ID and settings.
        
        This is called after __init__() and before start(). This is where
        you should perform initialization that requires the instance ID or
        settings.
        
        Args:
            instance_id: Unique identifier for this plugin instance.
            settings: Dictionary of settings from the schema.
        """
        self._instance_id = instance_id
        self._settings = settings.copy()
        self._state = PluginState.INITIALIZED
    
    def start(self) -> None:
        """Start the plugin.
        
        This is called when the plugin should begin operation. Start timers,
        subscribe to data sources, etc. The widget has already been created
        and is being displayed.
        
        Default implementation just changes state to STARTED.
        Override this if you need to start timers or other resources.
        """
        if self._state == PluginState.INITIALIZED or self._state == PluginState.STOPPED:
            self._state = PluginState.STARTED
    
    def stop(self) -> None:
        """Stop the plugin temporarily.
        
        This is called when the plugin should pause operation (e.g., when
        switching to a different page). Stop timers, unsubscribe from data
        sources, but keep state for potential resume.
        
        Default implementation just changes state to STOPPED.
        Override this if you have timers or subscriptions to clean up.
        """
        if self._state == PluginState.STARTED:
            self._state = PluginState.STOPPED
    
    def update(self, settings: Dict[str, Any]) -> None:
        """Update plugin with new settings.
        
        This is called when the user changes settings through the UI.
        The plugin should update its display accordingly.
        
        Args:
            settings: New settings dictionary.
        """
        self._settings = settings.copy()
        # Subclasses should override to apply new settings
    
    def dispose(self) -> None:
        """Dispose of the plugin and clean up resources.
        
        This is called when the plugin is being removed. Clean up all
        resources (timers, connections, etc.) here.
        
        Default implementation just changes state to DISPOSED.
        Override this if you have resources to clean up.
        """
        if self._state != PluginState.DISPOSED:
            self.stop()
            self._state = PluginState.DISPOSED
    
    def handle_error(self, error_msg: str) -> None:
        """Handle an error that occurred in the plugin.
        
        Args:
            error_msg: Description of the error.
        """
        self._state = PluginState.ERROR
        self.error_occurred.emit(error_msg)


class PluginMetadata:
    """Metadata about a plugin from its manifest."""
    
    def __init__(
        self,
        plugin_id: str,
        name: str,
        version: str,
        description: str,
        author: str,
        module_path: str,
        class_name: str,
        schema_path: Optional[str] = None,
        icon_path: Optional[str] = None,
        min_width: int = 1,
        min_height: int = 1,
        max_width: int = 8,
        max_height: int = 8,
        default_width: int = 2,
        default_height: int = 2
    ) -> None:
        """Initialize plugin metadata.
        
        Args:
            plugin_id: Unique identifier for the plugin.
            name: Display name.
            version: Version string (e.g., "1.0.0").
            description: Short description.
            author: Plugin author.
            module_path: Python module path (e.g., "examples.clock_widget").
            class_name: Name of the PluginBase subclass.
            schema_path: Path to settings schema JSON file.
            icon_path: Path to plugin icon.
            min_width: Minimum tile width in grid cells.
            min_height: Minimum tile height in grid cells.
            max_width: Maximum tile width in grid cells.
            max_height: Maximum tile height in grid cells.
            default_width: Default tile width.
            default_height: Default tile height.
        """
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.module_path = module_path
        self.class_name = class_name
        self.schema_path = schema_path
        self.icon_path = icon_path
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height
        self.default_width = default_width
        self.default_height = default_height
    
    def __repr__(self) -> str:
        return f"PluginMetadata(id={self.plugin_id}, name={self.name}, version={self.version})"