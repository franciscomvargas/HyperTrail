"""
WebSocket client for L2 order book integration.
Provides async reconnection, market data caching.
Uses direct imports to avoid package-relative import issues.
"""

import logging
from datetime import datetime
from typing import Dict, Callable, Any, Optional

# Direct imports
from constants import KEEPALIVE_PING_SECONDS


logger = logging.getLogger(__name__)


class L2WebSocketClient:
    """Async WebSocket client for Hyperliquid L2 order book integration."""
    
    def __init__(self):
        self._connected = False
        self._subscriptions: Dict[str, bool] = {}  # coin -> subscribed status
        self._market_data: Dict[str, Any] = {}     # coin -> latest snapshot
        self._callbacks: Dict[str, list[Callable]] = {}  # coin -> callbacks
        
    def is_connected(self) -> bool:
        """Check WebSocket connection status."""
        return self._connected
    
    def get_all_subscribed_coins(self) -> list[str]:
        """Get list of all currently subscribed coins."""
        return [coin for coin, subscribed in self._subscriptions.items() if subscribed]

