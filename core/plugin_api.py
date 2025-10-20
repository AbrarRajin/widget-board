"""Plugin API and base classes.

This module defines the contract between the host application and plugins.
Supports both in-process and out-of-process (IPC) execution modes.
"""

from typing import Any, Dict, Optional
from enum import Enum
from abc import ABCMeta
from PySide6.QtCore import QObject, Signal


class ExecutionMode(str, Enum):
    """Plugin execution modes."""
    
    IN_PROCESS = "in_process"      # Plugin runs in same process
    OUT_OF_PROCESS = "out_of_process"  # Plugin runs in separate process


class PluginState(str, Enum):
    """Plugin lifecycle states."""
    
    CREATED = "created"
    INITIALIZED = "initialized"
    STARTED = "started"
    STOPPED = "stopped"
    ERROR = "error"
    DISPOSED = "disposed"


# Combined metaclass for ABC + QObject
class PluginMeta(ABCMeta, type(QObject)):
    """Metaclass that combines ABC and QObject metaclasses."""
    pass


class WidgetPlugin(QObject, metaclass=PluginMeta):
    """Base class for all widget plugins.
    
    This class defines the lifecycle and interface that all plugins must implement.
    Plugins can run either in-process or out-of-process depending on their manifest.
    """
    
    # Signals
    render_updated = Signal()  # Emitted when plugin needs to re-render
    error_occurred = Signal(str)  # Emitted when an error occurs
    
    def __init__(
        self,
        instance_id: str,
        plugin_id: str,
        metadata: "PluginMetadata",
        settings: Dict[str, Any]
    ) -> None:
        """Initialize plugin.
        
        Args:
            instance_id: Unique instance identifier
            plugin_id: Plugin type identifier
            metadata: Plugin metadata from manifest
            settings: Initial settings dictionary
        """
        super().__init__()
        self.instance_id = instance_id
        self.plugin_id = plugin_id
        self.metadata = metadata
        self.settings = settings
        self._state = PluginState.CREATED
    
    @property
    def state(self) -> PluginState:
        """Get current plugin state."""
        return self._state
    
    def init(self) -> None:
        """Initialize the plugin.
        
        Called once when the plugin is first loaded. Set up initial state,
        load resources, but don't start timers or data fetching yet.
        """
        self._state = PluginState.INITIALIZED
    
    def start(self) -> None:
        """Start the plugin lifecycle.
        
        Called when the plugin should become active. Start timers,
        begin data fetching, subscribe to events, etc.
        """
        if self._state == PluginState.INITIALIZED or self._state == PluginState.STOPPED:
            self._state = PluginState.STARTED
    
    def stop(self) -> None:
        """Stop the plugin lifecycle.
        
        Called when the plugin should pause. Stop timers, unsubscribe
        from events, but keep state for potential resume.
        """
        if self._state == PluginState.STARTED:
            self._state = PluginState.STOPPED
    
    def update(self, delta_time: float) -> None:
        """Update plugin state (called periodically).
        
        Args:
            delta_time: Time since last update in seconds
        """
        pass
    
    def get_render_data(self) -> Dict[str, Any]:
        """Get render data for this plugin.
        
        Returns:
            Dictionary containing render information. Must include at least:
            - 'html': HTML content to display
            - Optional: 'css': CSS styles
            - Optional: 'needs_update': bool indicating if continuous updates needed
        """
        return {"html": "<div>No content</div>"}
    
    def on_settings_changed(self, new_settings: Dict[str, Any]) -> None:
        """Handle settings change.
        
        Called when user changes plugin settings through the UI.
        
        Args:
            new_settings: New settings dictionary
        """
        self.settings = new_settings
        self.render_updated.emit()
    
    def dispose(self) -> None:
        """Dispose of the plugin and clean up resources.
        
        Called when plugin is being removed. Clean up all resources
        (timers, connections, threads, etc.) here.
        """
        if self._state != PluginState.DISPOSED:
            self.stop()
            self._state = PluginState.DISPOSED


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
        execution_mode: ExecutionMode = ExecutionMode.IN_PROCESS,
        worker_script: Optional[str] = None,
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
            plugin_id: Unique identifier for the plugin
            name: Display name
            version: Version string (e.g., "1.0.0")
            description: Short description
            author: Plugin author
            module_path: Python module path (e.g., "examples.clock_widget")
            class_name: Name of the WidgetPlugin subclass
            execution_mode: IN_PROCESS or OUT_OF_PROCESS
            worker_script: Path to worker script (required for OUT_OF_PROCESS)
            schema_path: Path to settings schema JSON file
            icon_path: Path to plugin icon
            min_width: Minimum tile width in grid cells
            min_height: Minimum tile height in grid cells
            max_width: Maximum tile width in grid cells
            max_height: Maximum tile height in grid cells
            default_width: Default tile width
            default_height: Default tile height
        """
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.module_path = module_path
        self.class_name = class_name
        self.execution_mode = execution_mode
        self.worker_script = worker_script
        self.schema_path = schema_path
        self.icon_path = icon_path
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height
        self.default_width = default_width
        self.default_height = default_height
    
    def __repr__(self) -> str:
        return f"PluginMetadata(id={self.plugin_id}, name={self.name}, mode={self.execution_mode})"