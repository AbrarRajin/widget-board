"""Plugin worker process template.

This module runs in a separate process and hosts a single plugin instance.
"""

import logging
import sys
import traceback
import zmq
from typing import Optional
from pathlib import Path

from ipc.message_schema import IPCMessage, MessageType, ErrorMessage
from ipc.zmq_transport import ZMQTransport
from core.plugin_api import WidgetPlugin

logger = logging.getLogger(__name__)


class PluginWorker:
    """Worker process that hosts a plugin instance."""
    
    def __init__(self, endpoint: str, instance_id: str):
        """Initialize plugin worker.
        
        Args:
            endpoint: ZMQ endpoint to bind to
            instance_id: Unique instance identifier
        """
        self.endpoint = endpoint
        self.instance_id = instance_id
        self.plugin: Optional[WidgetPlugin] = None
        self.transport: Optional[ZMQTransport] = None
        self.running = True
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def run(self):
        """Main worker loop."""
        try:
            # Create transport (REP socket)
            self.transport = ZMQTransport(zmq.REP, self.endpoint, bind=True)
            logger.info(f"Plugin worker started (instance: {self.instance_id})")
            
            # Main message loop
            while self.running:
                # Receive message
                message = self.transport.receive(timeout_ms=1000)
                
                if message is None:
                    continue
                
                # Process message
                response = self._handle_message(message)
                
                # Send response
                if response:
                    self.transport.send(response, timeout_ms=5000)
            
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
        
        finally:
            self._cleanup()
    
    def _handle_message(self, message: IPCMessage) -> Optional[IPCMessage]:
        """Handle incoming message.
        
        Args:
            message: Received message
            
        Returns:
            Response message
        """
        try:
            if message.type == MessageType.INIT:
                return self._handle_init(message)
            
            elif message.type == MessageType.START:
                return self._handle_start(message)
            
            elif message.type == MessageType.UPDATE:
                return self._handle_update(message)
            
            elif message.type == MessageType.RENDER:
                return self._handle_render(message)
            
            elif message.type == MessageType.SETTINGS_CHANGED:
                return self._handle_settings_changed(message)
            
            elif message.type == MessageType.DISPOSE:
                return self._handle_dispose(message)
            
            elif message.type == MessageType.SHUTDOWN:
                return self._handle_shutdown(message)
            
            else:
                logger.warning(f"Unknown message type: {message.type}")
                return ErrorMessage(self.instance_id, f"Unknown message type: {message.type}")
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            return ErrorMessage(
                self.instance_id,
                str(e),
                traceback.format_exc()
            )
    
    def _handle_init(self, message: IPCMessage) -> IPCMessage:
        """Handle INIT message."""
        plugin_id = message.payload["plugin_id"]
        settings = message.payload["settings"]
        
        logger.info(f"Initializing plugin: {plugin_id}")
        
        # Create plugin instance (must be implemented by subclass)
        self.plugin = self._create_plugin_instance(plugin_id, settings)
        
        if self.plugin is None:
            return ErrorMessage(self.instance_id, f"Failed to create plugin: {plugin_id}")
        
        # Initialize plugin
        self.plugin.init()
        
        return IPCMessage(
            type=MessageType.INIT,
            instance_id=self.instance_id,
            payload={"status": "ok"}
        )
    
    def _handle_start(self, message: IPCMessage) -> IPCMessage:
        """Handle START message."""
        if self.plugin is None:
            return ErrorMessage(self.instance_id, "Plugin not initialized")
        
        logger.info("Starting plugin")
        self.plugin.start()
        
        return IPCMessage(
            type=MessageType.START,
            instance_id=self.instance_id,
            payload={"status": "ok"}
        )
    
    def _handle_update(self, message: IPCMessage) -> IPCMessage:
        """Handle UPDATE message."""
        if self.plugin is None:
            return ErrorMessage(self.instance_id, "Plugin not initialized")
        
        delta_time = message.payload["delta_time"]
        self.plugin.update(delta_time)
        
        return IPCMessage(
            type=MessageType.UPDATE,
            instance_id=self.instance_id,
            payload={"status": "ok"}
        )
    
    def _handle_render(self, message: IPCMessage) -> IPCMessage:
        """Handle RENDER message."""
        if self.plugin is None:
            return ErrorMessage(self.instance_id, "Plugin not initialized")
        
        width = message.payload["width"]
        height = message.payload["height"]
        
        # Get render output from plugin
        render_data = self.plugin.get_render_data()
        
        return IPCMessage(
            type=MessageType.RENDER,
            instance_id=self.instance_id,
            payload={
                "render_data": render_data,
                "width": width,
                "height": height,
            }
        )
    
    def _handle_settings_changed(self, message: IPCMessage) -> IPCMessage:
        """Handle SETTINGS_CHANGED message."""
        if self.plugin is None:
            return ErrorMessage(self.instance_id, "Plugin not initialized")
        
        settings = message.payload["settings"]
        logger.info(f"Updating settings: {settings}")
        
        self.plugin.on_settings_changed(settings)
        
        return IPCMessage(
            type=MessageType.SETTINGS_CHANGED,
            instance_id=self.instance_id,
            payload={"status": "ok"}
        )
    
    def _handle_dispose(self, message: IPCMessage) -> IPCMessage:
        """Handle DISPOSE message."""
        if self.plugin is not None:
            logger.info("Disposing plugin")
            self.plugin.dispose()
            self.plugin = None
        
        return IPCMessage(
            type=MessageType.DISPOSE,
            instance_id=self.instance_id,
            payload={"status": "ok"}
        )
    
    def _handle_shutdown(self, message: IPCMessage) -> IPCMessage:
        """Handle SHUTDOWN message."""
        logger.info("Shutting down worker")
        self.running = False
        
        return IPCMessage(
            type=MessageType.SHUTDOWN,
            instance_id=self.instance_id,
            payload={"status": "ok"}
        )
    
    def _create_plugin_instance(self, plugin_id: str, settings: dict) -> Optional[WidgetPlugin]:
        """Create plugin instance (must be overridden by specific worker).
        
        Args:
            plugin_id: Plugin identifier
            settings: Plugin settings
            
        Returns:
            Plugin instance, or None on error
        """
        raise NotImplementedError("Subclass must implement _create_plugin_instance")
    
    def _cleanup(self):
        """Cleanup resources."""
        if self.plugin:
            try:
                self.plugin.dispose()
            except Exception as e:
                logger.error(f"Error disposing plugin: {e}")
        
        if self.transport:
            self.transport.close()


def main():
    """Worker process entry point."""
    if len(sys.argv) < 3:
        print("Usage: python worker.py <endpoint> <instance_id>")
        sys.exit(1)
    
    endpoint = sys.argv[1]
    instance_id = sys.argv[2]
    
    worker = PluginWorker(endpoint, instance_id)
    worker.run()


if __name__ == "__main__":
    main()
