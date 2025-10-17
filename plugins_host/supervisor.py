"""Plugin process supervisor.

This module manages the lifecycle of plugin worker processes.
"""

import logging
import subprocess
import sys
import time
import zmq
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

from ipc.message_schema import (
    IPCMessage, InitMessage, StartMessage, UpdateMessage,
    DisposeMessage, RenderMessage, SettingsChangedMessage,
    ShutdownMessage, MessageType
)
from ipc.zmq_transport import ZMQTransport

logger = logging.getLogger(__name__)


@dataclass
class PluginProcess:
    """Information about a running plugin process."""
    
    instance_id: str
    plugin_id: str
    process: subprocess.Popen
    transport: ZMQTransport
    endpoint: str
    started: float
    last_heartbeat: float


class PluginSupervisor:
    """Manages out-of-process plugin worker processes."""
    
    def __init__(self, base_port: int = 5555):
        """Initialize plugin supervisor.
        
        Args:
            base_port: Base port number for ZMQ endpoints
        """
        self.base_port = base_port
        self.processes: Dict[str, PluginProcess] = {}
        self._next_port = base_port
    
    def spawn_plugin(
        self,
        instance_id: str,
        plugin_id: str,
        worker_script: Path,
        settings: Dict
    ) -> bool:
        """Spawn a new plugin worker process.
        
        Args:
            instance_id: Unique instance identifier
            plugin_id: Plugin type identifier
            worker_script: Path to worker Python script
            settings: Plugin settings dictionary
            
        Returns:
            True if spawned successfully
        """
        if instance_id in self.processes:
            logger.warning(f"Plugin instance {instance_id} already running")
            return False
        
        # Allocate port and create endpoint
        port = self._next_port
        self._next_port += 1
        endpoint = f"tcp://127.0.0.1:{port}"
        
        try:
            # Start worker process
            logger.info(f"Spawning plugin worker: {plugin_id} (instance: {instance_id})")
            logger.info(f"Worker script: {worker_script}")
            logger.info(f"Endpoint: {endpoint}")
            
            process = subprocess.Popen(
                [sys.executable, str(worker_script), endpoint, instance_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            # Give process time to start
            time.sleep(0.5)
            
            # Check if process started
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logger.error(f"Worker process failed to start: {stderr}")
                return False
            
            # Create transport to communicate with worker
            transport = ZMQTransport(zmq.REQ, endpoint, bind=False)
            
            # Send INIT message
            init_msg = InitMessage(instance_id, plugin_id, settings)
            response = transport.send_and_receive(init_msg, timeout_ms=5000)
            
            if not response or response.type == MessageType.ERROR:
                logger.error(f"Failed to initialize plugin: {response.payload if response else 'timeout'}")
                transport.close()
                process.terminate()
                return False
            
            # Send START message
            start_msg = StartMessage(instance_id)
            response = transport.send_and_receive(start_msg, timeout_ms=5000)
            
            if not response or response.type == MessageType.ERROR:
                logger.error(f"Failed to start plugin: {response.payload if response else 'timeout'}")
                transport.close()
                process.terminate()
                return False
            
            # Store process info
            self.processes[instance_id] = PluginProcess(
                instance_id=instance_id,
                plugin_id=plugin_id,
                process=process,
                transport=transport,
                endpoint=endpoint,
                started=time.time(),
                last_heartbeat=time.time(),
            )
            
            logger.info(f"Plugin {plugin_id} spawned successfully (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Error spawning plugin: {e}", exc_info=True)
            return False
    
    def send_update(self, instance_id: str, delta_time: float) -> bool:
        """Send update message to plugin.
        
        Args:
            instance_id: Plugin instance ID
            delta_time: Time since last update
            
        Returns:
            True if sent successfully
        """
        if instance_id not in self.processes:
            return False
        
        proc = self.processes[instance_id]
        msg = UpdateMessage(instance_id, delta_time)
        response = proc.transport.send_and_receive(msg, timeout_ms=100)
        
        return response is not None and response.type != MessageType.ERROR
    
    def request_render(self, instance_id: str, width: int, height: int) -> Optional[Dict]:
        """Request render output from plugin.
        
        Args:
            instance_id: Plugin instance ID
            width: Render width
            height: Render height
            
        Returns:
            Render data dictionary, or None on error
        """
        if instance_id not in self.processes:
            return None
        
        proc = self.processes[instance_id]
        msg = RenderMessage(instance_id, width, height)
        response = proc.transport.send_and_receive(msg, timeout_ms=500)
        
        if response and response.type != MessageType.ERROR:
            return response.payload
        
        return None
    
    def update_settings(self, instance_id: str, settings: Dict) -> bool:
        """Update plugin settings.
        
        Args:
            instance_id: Plugin instance ID
            settings: New settings dictionary
            
        Returns:
            True if updated successfully
        """
        if instance_id not in self.processes:
            return False
        
        proc = self.processes[instance_id]
        msg = SettingsChangedMessage(instance_id, settings)
        response = proc.transport.send_and_receive(msg, timeout_ms=1000)
        
        return response is not None and response.type != MessageType.ERROR
    
    def terminate_plugin(self, instance_id: str) -> None:
        """Terminate a plugin worker process.
        
        Args:
            instance_id: Plugin instance ID
        """
        if instance_id not in self.processes:
            return
        
        proc = self.processes[instance_id]
        
        try:
            # Send shutdown message
            shutdown_msg = ShutdownMessage(instance_id)
            proc.transport.send(shutdown_msg, timeout_ms=1000)
            
            # Wait for graceful shutdown
            try:
                proc.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                logger.warning(f"Plugin {instance_id} didn't shut down gracefully, terminating")
                proc.process.terminate()
                try:
                    proc.process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    logger.error(f"Plugin {instance_id} didn't terminate, killing")
                    proc.process.kill()
            
            # Close transport
            proc.transport.close()
            
            logger.info(f"Plugin {instance_id} terminated")
            
        except Exception as e:
            logger.error(f"Error terminating plugin {instance_id}: {e}")
        
        finally:
            del self.processes[instance_id]
    
    def check_health(self) -> None:
        """Check health of all running plugins and restart if needed."""
        for instance_id in list(self.processes.keys()):
            proc = self.processes[instance_id]
            
            # Check if process is still alive
            if proc.process.poll() is not None:
                logger.error(f"Plugin {instance_id} process died unexpectedly")
                self.terminate_plugin(instance_id)
                # TODO: Implement auto-restart logic
    
    def shutdown_all(self) -> None:
        """Shutdown all plugin processes."""
        logger.info("Shutting down all plugin processes")
        for instance_id in list(self.processes.keys()):
            self.terminate_plugin(instance_id)
    
    def __del__(self):
        """Cleanup on deletion."""
        self.shutdown_all()
