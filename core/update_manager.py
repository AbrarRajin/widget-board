"""Manages plugin update requests with throttling and coalescing."""
from typing import Dict, Callable, Optional, Set
from PySide6.QtCore import QObject, QTimer, Signal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class UpdateRequest:
    """Pending update request for a plugin instance."""
    instance_id: str
    reason: str
    requested_at: datetime
    coalesced_count: int = 0


@dataclass
class ThrottleConfig:
    """Throttling configuration per instance."""
    min_interval_ms: int = 1000  # Minimum time between updates
    max_pending: int = 3  # Max queued requests before dropping
    coalesce_window_ms: int = 100  # Time window to coalesce requests


class UpdateManager(QObject):
    """
    Manages plugin update requests with throttling and coalescing.
    
    - Coalesces multiple rapid requests into one
    - Throttles updates to minimum interval
    - Drops excess pending requests
    - Prioritizes visible page updates
    """
    
    update_dispatched = Signal(str, str)  # instance_id, reason
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        # Throttle configs per instance
        self._configs: Dict[str, ThrottleConfig] = {}
        
        # Last update time per instance
        self._last_update: Dict[str, datetime] = {}
        
        # Pending requests
        self._pending: Dict[str, UpdateRequest] = {}
        
        # Currently visible page instances
        self._visible_instances: Set[str] = set()
        
        # Processing timer
        self._process_timer = QTimer(self)
        self._process_timer.timeout.connect(self._process_queue)
        self._process_timer.start(50)  # Check every 50ms
        
        logger.info("UpdateManager initialized")
    
    def set_throttle_config(self, instance_id: str, config: ThrottleConfig) -> None:
        """Set throttling configuration for an instance."""
        self._configs[instance_id] = config
    
    def request_update(self, instance_id: str, reason: str = "user") -> None:
        """
        Request an update for a plugin instance.
        
        Args:
            instance_id: Plugin instance identifier
            reason: Update reason ("timer", "user", "resume", etc.)
        """
        now = datetime.now()
        
        # Get or create config
        config = self._configs.get(instance_id, ThrottleConfig())
        
        # Check if we should coalesce with existing pending request
        if instance_id in self._pending:
            request = self._pending[instance_id]
            time_since_request = (now - request.requested_at).total_seconds() * 1000
            
            if time_since_request < config.coalesce_window_ms:
                # Coalesce: just increment counter
                request.coalesced_count += 1
                logger.debug(f"Coalesced update for {instance_id} (count: {request.coalesced_count})")
                return
        
        # Check pending queue size
        if instance_id in self._pending:
            if self._pending[instance_id].coalesced_count >= config.max_pending:
                logger.warning(f"Dropping update request for {instance_id} (queue full)")
                return
        
        # Add to pending
        self._pending[instance_id] = UpdateRequest(
            instance_id=instance_id,
            reason=reason,
            requested_at=now
        )
        
        logger.debug(f"Update requested for {instance_id} (reason: {reason})")
    
    def set_visible_instances(self, instance_ids: Set[str]) -> None:
        """Update the set of currently visible instances (for prioritization)."""
        self._visible_instances = instance_ids
        logger.debug(f"Visible instances updated: {len(instance_ids)} visible")
    
    def _process_queue(self) -> None:
        """Process pending update requests respecting throttles."""
        now = datetime.now()
        
        # Sort: prioritize visible instances
        pending_items = list(self._pending.items())
        pending_items.sort(key=lambda x: x[0] not in self._visible_instances)
        
        dispatched = []
        
        for instance_id, request in pending_items:
            config = self._configs.get(instance_id, ThrottleConfig())
            
            # Check throttle
            if instance_id in self._last_update:
                elapsed_ms = (now - self._last_update[instance_id]).total_seconds() * 1000
                if elapsed_ms < config.min_interval_ms:
                    # Still throttled
                    continue
            
            # Dispatch update
            self._last_update[instance_id] = now
            dispatched.append(instance_id)
            self.update_dispatched.emit(instance_id, request.reason)
            
            logger.debug(
                f"Dispatched update for {instance_id} "
                f"(coalesced {request.coalesced_count} requests)"
            )
        
        # Remove dispatched from pending
        for instance_id in dispatched:
            del self._pending[instance_id]
    
    def clear_pending(self, instance_id: str) -> None:
        """Clear any pending updates for an instance."""
        if instance_id in self._pending:
            del self._pending[instance_id]
    
    def reset_throttle(self, instance_id: str) -> None:
        """Reset throttle timer for an instance (allows immediate update)."""
        if instance_id in self._last_update:
            del self._last_update[instance_id]