"""ZeroMQ transport layer for IPC communication.

This module provides the low-level transport using ZeroMQ sockets.
"""

import logging
import zmq
from typing import Optional, Callable
from .message_schema import IPCMessage

logger = logging.getLogger(__name__)


class ZMQTransport:
    """ZeroMQ transport for sending/receiving IPC messages."""
    
    def __init__(self, socket_type: int, endpoint: str, bind: bool = False):
        """Initialize ZMQ transport.
        
        Args:
            socket_type: ZMQ socket type (REQ, REP, DEALER, ROUTER, etc.)
            endpoint: ZMQ endpoint (e.g., "tcp://127.0.0.1:5555" or "ipc:///tmp/plugin.ipc")
            bind: If True, bind to endpoint; if False, connect to endpoint
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(socket_type)
        self.endpoint = endpoint
        self.is_bound = bind
        
        if bind:
            self.socket.bind(endpoint)
            logger.info(f"ZMQ socket bound to {endpoint}")
        else:
            self.socket.connect(endpoint)
            logger.info(f"ZMQ socket connected to {endpoint}")
    
    def send(self, message: IPCMessage, timeout_ms: int = 5000) -> bool:
        """Send a message.
        
        Args:
            message: Message to send
            timeout_ms: Send timeout in milliseconds
            
        Returns:
            True if sent successfully, False on timeout
        """
        try:
            self.socket.setsockopt(zmq.SNDTIMEO, timeout_ms)
            json_str = message.to_json()
            self.socket.send_string(json_str)
            logger.debug(f"Sent {message.type} message for instance {message.instance_id}")
            return True
        except zmq.Again:
            logger.warning(f"Send timeout for {message.type} message")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def receive(self, timeout_ms: int = 5000) -> Optional[IPCMessage]:
        """Receive a message.
        
        Args:
            timeout_ms: Receive timeout in milliseconds
            
        Returns:
            Received message, or None on timeout
        """
        try:
            self.socket.setsockopt(zmq.RCVTIMEO, timeout_ms)
            json_str = self.socket.recv_string()
            message = IPCMessage.from_json(json_str)
            logger.debug(f"Received {message.type} message for instance {message.instance_id}")
            return message
        except zmq.Again:
            logger.debug("Receive timeout")
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    def send_and_receive(self, message: IPCMessage, timeout_ms: int = 5000) -> Optional[IPCMessage]:
        """Send a message and wait for a response (REQ/REP pattern).
        
        Args:
            message: Message to send
            timeout_ms: Timeout in milliseconds
            
        Returns:
            Response message, or None on timeout/error
        """
        if not self.send(message, timeout_ms):
            return None
        return self.receive(timeout_ms)
    
    def close(self) -> None:
        """Close the transport."""
        logger.info(f"Closing ZMQ transport for {self.endpoint}")
        self.socket.close()
        self.context.term()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
