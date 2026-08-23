"""
Tests for engine/state_machine.py - Trailing logic and state transitions.
"""

import pytest
from datetime import datetime

pytest_plugins = ['conftest']


@pytest.fixture(autouse=True)
def reset_static_state():
    """Reset module-level static state between tests."""
    from engine.state_machine import TrailingStateMachine
    
    # Clear tracked states after each test
    yield
    
    # Reset tracking dictionaries
    if hasattr(TrailingStateMachine, '_instance_cache'):
        TrailingStateMachine._instance_cache.clear()


class TestStateTransitionValidator:
    """Test state transition validation logic."""
    
    def test_valid_trailing_to_locked_transition(self):
        from engine.state_machine import StateTransitionValidator
        from engine.models import BotStatus
        
        can_transition, reason = StateTransitionValidator.can_transition(
            BotStatus.TRAILING, 
            BotStatus.LOCKED
        )
        assert can_transition is True
        assert "valid transition" in reason
    
    def test_invalid_state_transition(self):
        from engine.state_machine import StateTransitionValidator
        from engine.models import BotStatus
        
        # Can't transition directly from TRAILING to FILLED
        can_transition, reason = StateTransitionValidator.can_transition(
            BotStatus.TRAILING, 
            BotStatus.FILLED
        )
        assert can_transition is False
        assert "invalid transition" in reason
    
    def test_terminal_state_detection(self):
        from engine.state_machine import StateTransitionValidator
        from engine.models import BotStatus
        
        is_terminal, reason = StateTransitionValidator.validate_final_state(
            BotStatus.FILLED
        )
        assert is_terminal is True
        
        # Another terminal state
        is_terminal, _ = StateTransitionValidator.validate_final_state(
            BotStatus.STOPPED
        )
        assert is_terminal is True
    
    def test_non_terminal_state(self):
        from engine.state_machine import StateTransitionValidator
        from engine.models import BotStatus
        
        is_terminal, reason = StateTransitionValidator.validate_final_state(
            BotStatus.TRAILING
        )
        assert is_terminal is False


class TestTrailingStateMachine:
    """Test core trailing logic evaluation."""
    
    def test_buy_scenario_trailing_direction(self):
        """Test Long Entry (buy dip) trailing direction calculation."""
        from engine.state_machine import TrailingStateMachine, TrailingDirection
        from engine.models import TrailType
        
        sm = TrailingStateMachine()
        
        # Simulate current mid price of 60000 with 0.8% offset
        new_limit, direction = sm.evaluate_next_trail_price(
            current_mid_price=60000.0,
            bot_config_type=TrailType.LONG_ENTRY,
            offset_pct=0.8,
            is_descending=True
        )
        
        # Expected: 60000 * (1 - 0.008) = 59520
        expected_price = 60000.0 * (1 - 0.008)
        assert abs(new_limit - expected_price) < 0.01
        assert direction == TrailingDirection.DOWN
    
    def test_sell_scenario_trailing_direction(self):
        """Test Short Entry (sell rally) trailing direction."""
        from engine.state_machine import TrailingStateMachine, TrailingDirection
        from engine.models import TrailType
        
        sm = TrailingStateMachine()
        
        # Simulate current mid price of 3500 with 1.0% offset for selling up
        new_limit, direction = sm.evaluate_next_trail_price(
            current_mid_price=3500.0,
            bot_config_type=TrailType.SHORT_ENTRY,
            offset_pct=1.0,
            is_descending=False
        )
        
        # Expected: 3500 * (1 + 0.01) = 3535
        expected_price = 3500.0 * (1 + 0.01)
        assert abs(new_limit - expected_price) < 0.01
        assert direction == TrailingDirection.UP
    
    def test_max_chase_safety_check(self):
        """Test circuit breaker safety logic."""
        from engine.state_machine import TrailingStateMachine
        
        sm = TrailingStateMachine()
        
        # Simulate scenario where max chase is not exceeded
        should_stop, reason = sm.check_max_chase_safety(
            current_trail_reference=67900.0,
            max_chase_pct=1.5
        )
        
        # In this version, we check if the logic returns False (safe)
        assert should_stop is False
        
    def test_spread_safety_validation(self):
        """Test spread threshold validation."""
        from engine.state_machine import TrailingStateMachine
        
        sm = TrailingStateMachine()
        
        # Valid low spread
        is_safe, reason = sm.validate_spread_safety({
            "coin": "BTC",
            "current_price": 67900.0,
            "best_bid": 67895.0,
            "best_ask": 67905.0,
            "spread_pct": 0.0147,
            "timestamp": datetime.now()
        })
        
        assert is_safe is True
        
    def test_offset_range_validation(self):
        """Test that offset percentages are within limits."""
        from engine.state_machine import TrailingStateMachine
        
        sm = TrailingStateMachine()
        
        # Valid offset (within 0.1-5.0 range)
        is_valid, reason = sm.check_trail_distance_limit(2.5)
        assert is_valid is True
        
        # Invalid offset (exceeds maximum)
        is_valid, reason = sm.check_trail_distance_limit(6.0)
        assert is_valid is False
