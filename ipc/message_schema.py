"""IPC message protocol definitions.

This module defines the message schema for communication between
the host application and plugin worker processes.
"""

from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
import json


class MessageType(str, Enum):
    """Message types for IPC communication."""
    
    INIT = "init"                    # Initialize plugin
    START = "start"                  # Start plugin lifecycle
    UPDATE = "update"                # Update plugin state
    DISPOSE = "dispose"              # Dispose plugin resources
    RENDER = "render"                # Request render output
    SETTINGS_CHANGED = "settings_changed"  # Settings updated
    ERROR = "error"                  # Error occurred
    HEARTBEAT = "heartbeat"          # Process health check
    SHUTDOWN = "shutdown"            # Graceful shutdown


@dataclass
class IPCMessage:
    """Base IPC message."""
    
    type: MessageType
    instance_id: str
    payload: Dict[str, Any]
    
    def to_json(self) -> str:
        """Serialize message to JSON."""
        data = {
            "type": self.type.value,
            "instance_id": self.instance_id,
            "payload": self.payload,
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "IPCMessage":
        """Deserialize message from JSON."""
        data = json.loads(json_str)
        return cls(
            type=MessageType(data["type"]),
            instance_id=data["instance_id"],
            payload=data["payload"],
        )


@dataclass
class InitMessage(IPCMessage):
    """Initialize plugin message."""
    
    def __init__(self, instance_id: str, plugin_id: str, settings: Dict[str, Any]):
        super().__init__(
            type=MessageType.INIT,
            instance_id=instance_id,
            payload={
                "plugin_id": plugin_id,
                "settings": settings,
            }
        )


@dataclass
class StartMessage(IPCMessage):
    """Start plugin lifecycle message."""
    
    def __init__(self, instance_id: str):
        super().__init__(
            type=MessageType.START,
            instance_id=instance_id,
            payload={},
        )


@dataclass
class UpdateMessage(IPCMessage):
    """Update plugin state message."""
    
    def __init__(self, instance_id: str, delta_time: float):
        super().__init__(
            type=MessageType.UPDATE,
            instance_id=instance_id,
            payload={"delta_time": delta_time},
        )


@dataclass
class DisposeMessage(IPCMessage):
    """Dispose plugin resources message."""
    
    def __init__(self, instance_id: str):
        super().__init__(
            type=MessageType.DISPOSE,
            instance_id=instance_id,
            payload={},
        )


@dataclass
class RenderMessage(IPCMessage):
    """Request render output message."""
    
    def __init__(self, instance_id: str, width: int, height: int):
        super().__init__(
            type=MessageType.RENDER,
            instance_id=instance_id,
            payload={"width": width, "height": height},
        )


@dataclass
class SettingsChangedMessage(IPCMessage):
    """Settings updated message."""
    
    def __init__(self, instance_id: str, settings: Dict[str, Any]):
        super().__init__(
            type=MessageType.SETTINGS_CHANGED,
            instance_id=instance_id,
            payload={"settings": settings},
        )


@dataclass
class ErrorMessage(IPCMessage):
    """Error occurred message."""
    
    def __init__(self, instance_id: str, error: str, traceback: Optional[str] = None):
        super().__init__(
            type=MessageType.ERROR,
            instance_id=instance_id,
            payload={
                "error": error,
                "traceback": traceback,
            }
        )


@dataclass
class HeartbeatMessage(IPCMessage):
    """Process health check message."""
    
    def __init__(self, instance_id: str):
        super().__init__(
            type=MessageType.HEARTBEAT,
            instance_id=instance_id,
            payload={},
        )


@dataclass
class ShutdownMessage(IPCMessage):
    """Graceful shutdown message."""
    
    def __init__(self, instance_id: str):
        super().__init__(
            type=MessageType.SHUTDOWN,
            instance_id=instance_id,
            payload={},
        )
