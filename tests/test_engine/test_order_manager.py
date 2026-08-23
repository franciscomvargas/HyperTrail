"""
Tests for engine/order_manager.py - Atomic order management operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytest_plugins = ['conftest']


class TestOrderManager:
    """Test atomic order modification and management."""
    
    @pytest.mark.asyncio
    async def test_place_trailing_order_success(self, mock_exchange, mock_info):
        """Verify successful order placement."""
        from engine.order_manager import OrderManager
        
        manager = OrderManager(mock_exchange, mock_info)
        
        result_status, oid = await manager.place_trailing_order(
            coin="BTC",
            is_buy=True,
            size_usd=100.0,
            target_price=67900.0,
            reduce_only=False
        )
        
        assert result_status == "ok"
        # OID should be extracted from mock response
        assert oid == 98765
    
    @pytest.mark.asyncio
    async def test_modify_order_single_success(self, mock_exchange, mock_info):
        """Verify single order modification."""
        from engine.order_manager import OrderManager
        
        manager = OrderManager(mock_exchange, mock_info)
        
        result_status, modified = await manager.modify_order_single(
            coin="BTC",
            oid=12345,
            new_price=67850.0,
            size_asset=0.0147
        )
        
        assert result_status == "ok"
        assert modified is True
    
    @pytest.mark.asyncio
    async def test_batch_modify_orders_multiple(self, mock_exchange, mock_info):
        """Verify batch atomic modifications."""
        from engine.order_manager import OrderManager
        
        manager = OrderManager(mock_exchange, mock_info)
        
        modifications = [
            {"token_name": "BTC", "oid": 12345, "price": 67800.0, "sz": 0.01},
            {"token_name": "ETH", "oid": 67890, "price": 3420.0, "sz": 0.5}
        ]
        
        results = await manager.batch_modify_orders(modifications)
        
        # All should be marked as ok or not_found based on mock response
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_cancel_order_success(self, mock_exchange, mock_info):
        """Verify order cancellation."""
        from engine.order_manager import OrderManager
        
        manager = OrderManager(mock_exchange, mock_info)
        
        result_status, success = await manager.cancel_order(
            coin="BTC",
            oid=98765
        )
        
        assert result_status == "ok"
        assert success is True
    
    @pytest.mark.asyncio
    async def test_retry_state_tracking(self, mock_exchange, mock_info):
        """Test retry mechanism for failed modifications."""
        from engine.order_manager import OrderManager
        
        manager = OrderManager(mock_exchange, mock_info)
        
        # Initially no retry state for this OID
        assert 98765 not in manager._retry_states


class TestOrderNotFoundDetection:
    """Test race condition detection logic."""
    
    def test_detects_not_found_error_patterns(self):
        from engine.order_manager import OrderManager
        
        manager = OrderManager(None, None)  # No need for actual exchange
        
        error_messages = [
            "no order with oid 12345",
            "order not in book",
            "invalid order id",
            "Order is still open after cancel",
        ]
        
        for msg in error_messages:
            assert manager._detect_order_not_found_error(msg) is True
    
    def test_non_not_found_errors_return_false(self):
        from engine.order_manager import OrderManager
        
        manager = OrderManager(None, None)
        
        non_matching_messages = [
            "Insufficient balance",
            "Market spread too high",
            "Rate limit exceeded"
        ]
        
        for msg in non_matching_messages:
            assert manager._detect_order_not_found_error(msg) is False


class TestOrderValidationEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_modification_list(self):
        from engine.order_manager import OrderManager
        
        manager = OrderManager(None, None)
        
        results = asyncio.run(manager.batch_modify_orders([]))
        
        assert results == {}


class TestInitializationError:
    """Test that invalid parameters are rejected."""
    
    def test_invalid_oid_rejection(self, mock_exchange, mock_info):
        """Verify that invalid parameters are rejected."""
        from engine.order_manager import OrderManager
        
        manager = OrderManager(mock_exchange, mock_info)
        
        # Invalid OID (0 or negative) should trigger early warning in real code
        # In this test we just verify the call doesn't crash
        result_status, modified = asyncio.run(manager.modify_order_single(
            coin="BTC",
            oid=0,  # Invalid
            new_price=67850.0,
            size_asset=0.0147
        ))
        
        # Should fail gracefully
        assert result_status != "ok"
