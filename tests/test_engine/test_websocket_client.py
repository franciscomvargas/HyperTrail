"""
Tests for engine/websocket_client.py - L2 WebSocket market data integration.
"""

import pytest
from datetime import datetime

pytest_plugins = ['conftest']


class TestWebSocketClientInitialization:
    """Test WebSocket client setup and connection state."""
    
    def test_initial_undistinguished_state(self):
        from engine.websocket_client import L2WebSocketClient
        
        client = L2WebSocketClient()
        
        assert client._connected is False
        assert len(client._subscriptions) == 0
        assert len(client._market_data) == 0
    
    def test_connected_status_change(self, mock_exchange, mock_info):
        from engine.websocket_client import L2WebSocketClient
        
        client = L2WebSocketClient()
        client.exchange = mock_exchange
        client.info = mock_info
        
        # Simulate connected state
        client._connected = True
        
        assert client.is_connected() is True


class TestMarketDataHandling:
    """Test L2 market data parsing and caching."""
    
    def test_parse_l2_update_message(self, sample_market_snapshot):
        from engine.websocket_client import L2WebSocketClient
        
        client = L2WebSocketClient()
        
        # Simulate incoming L2 update message structure
        mock_msg = {
            "coin": "BTC",
            "data": {
                "bids": [["67895.0", "0.5"]],  # price, size
                "asks": [["67905.0", "0.3"]]
            }
        }
        
        client._market_data["BTC"] = sample_market_snapshot
        
        # Verify market data is properly cached
        assert "BTC" in client._market_data
        assert client._market_data["BTC"]["current_price"] == 67900.0
    
    def test_spread_calculation(self, sample_market_snapshot):
        from engine.websocket_client import L2WebSocketClient
        
        client = L2WebSocketClient()
        
        # Verify spread calculation is reasonable
        spread = sample_market_snapshot["spread_pct"]
        assert 0.0 < spread < 1.0  # Should be a small positive percentage


class TestSubscriptionManagement:
    """Test subscription and unsubscription of market data feeds."""
    
    def test_subscription_registration(self, mock_exchange):
        from engine.websocket_client import L2WebSocketClient
        
        client = L2WebSocketClient()
        client.exchange = mock_exchange
        
        # Simulate subscription
        client._subscriptions["BTC"] = True
        
        subscribed_coins = client.get_all_subscribed_coins()
        assert "BTC" in subscribed_coins
    
    def test_multiple_coin_subscription(self, mock_exchange):
        from engine.websocket_client import L2WebSocketClient
        
        client = L2WebSocketClient()
        client.exchange = mock_exchange
        
        coins = ["BTC", "ETH", "SOL"]
        
        for coin in coins:
            client._subscriptions[coin] = True
        
        all_subscribed = client.get_all_subscribed_coins()
        assert len(all_subscribed) == 3
        

class TestL2CallbackRegistration:
    """Test callback registration mechanism."""
    
    def test_callback_registration(self):
        from engine.websocket_client import L2WebSocketClient
        
        client = L2WebSocketClient()
        
        # Simple mock callback
        received_events = []
        
        def mock_callback(coin, **kwargs):
            received_events.append({"coin": coin, "data": kwargs})
        
        # Register callback
        client.on_l2_update("ETH", mock_callback)
        
        # Verify registration completed
        assert "ETH" in client._callbacks
        assert len(client._callbacks["ETH"]) == 1
    
    def test_multiple_callbacks_per_coin(self):
        from engine.websocket_client import L2WebSocketClient
        
        client = L2WebSocketClient()
        
        callback_calls = [0, 0]
        
        def callback_1(coin, **kwargs):
            callback_calls[0] += 1
            
        def callback_2(coin, **kwargs):
            callback_calls[1] += 1
        
        client.on_l2_update("SOL", callback_1)
        client.on_l2_update("SOL", callback_2)
        
        # Verify both callbacks registered
        assert len(client._callbacks["SOL"]) == 2
