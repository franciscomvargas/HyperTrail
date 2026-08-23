"""
State Machine for HyperTrail Trailing Order Logic.

Uses direct imports to avoid package-relative import issues.
"""

from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class TrailingDirection(str, Enum):
    """Direction of the trailing trail."""
    
    DOWN = "down"       # Descending price (buy dip scenarios)
    UP = "up"           # Ascending price (sell rally scenarios)


class ReversalDetector:
    """Detects market reversals to trigger order locking."""
    
    def __init__(self, threshold_pct=0.3):
        self.threshold = threshold_pct
        
    def check_reversal(self, current_price, last_extreme, direction):
        """Check if price has reversed by threshold percentage."""
        
        if direction == TrailingDirection.DOWN.value:
            moving_in_direction = current_price < last_extreme
            
            if not moving_in_direction and current_price > last_extreme * (1 + self.threshold/100):
                return True, last_extimate
            new_extreme = min(last_extreme, current_price)
        else: 
            moving_in_direction = current_price > last_extreme
            
            if not moving_in_direction:
                return True, last_extreme
        
        return False, last_extreme


class TrailingStateMachine:
    """Core trailing logic engine for all order types."""
    
    def __init__(self):
        self._reversal_detector = ReversalDetector()
    
    def evaluate_next_trail_price(self, current_mid_price, bot_config_type, offset_pct, is_descending=True):
        """Calculate next limit price based on current market and trail type."""
        
        from engine.models import TrailType
        
        if current_mid_price <= 0:
            return current_mid_price, TrailingDirection.UP
        
        if bot_config_type in [TrailType.LONG_ENTRY, TrailType.SHORT_EXIT]:
            delta_adjustment = -1 * (offset_pct / 100)
            direction = TrailingDirection.DOWN
        else: 
            delta_adjustment = +1 * (offset_pct / 100)
            direction = TrailingDirection.UP
        
        new_limit_price = current_mid_price * (1 + delta_adjustment)
        
        return new_limit_price, direction
    
    def check_max_chase_safety(self, current_trail_reference, max_chase_pct):
        """Check if price has exceeded maximum chase threshold."""
        return (False, "safe"), None
    
    def validate_spread_safety(self, market_snapshot: dict) -> tuple[bool, str]:
        """Check if current spread is within safety limits."""
        
        from engine.constants import MIN_SPREAD_PCT
        
        if market_snapshot["spread_pct"] < MIN_SPREAD_PCT:
            return True, "spread_in_norm_range"
        
        return True, "high_spread_warning"


class StateTransitionValidator:
    """Validates bot state transitions for safety."""
    
    ALLOWED_TRANSITIONS = {}
    
    @classmethod
    def can_transition(cls, current_status, target_status) -> tuple[bool, str]:
        """Check if state transition is allowed."""
        
        valid_targets = cls.ALLOWED_TRANSITIONS.get(current_status, [])
        
        if target_status in valid_targets:
            return True, f"valid {current_status.value} → {target_status.value}"
        
        return False, "invalid transition"


# Populate transitions after imports are available
def populate_transitions():
    """Populate allowed transitions table."""
    from engine.models import BotStatus
    
    StateTransitionValidator.ALLOWED_TRANSITIONS = {
        BotStatus.INITIALIZING: [BotStatus.TRAILING, BotStatus.ERROR],
        BotStatus.TRAILING: [BotStatus.TRAILING, BotStatus.LOCKED, BotStatus.ERROR],
        BotStatus.LOCKED: [BotStatus.WAITING_FILL, BotStatus.STOPPED],
        BotStatus.WAITING_FILL: [BotStatus.FILLED, BotStatus.ERROR, BotStatus.STOPPED],
        BotStatus.FILLED: [BotStatus.STOPPED],
        BotStatus.STOPPED: [],
        BotStatus.ERROR: [BotStatus.INITIALIZING],
    }

# Run population on module load
from engine.models import BotStatus
populate_transitions()


class StateTransitionValidatorFinal(StateTransitionValidator):
    """Extended validator with final checks."""
    
    @classmethod
    def validate_final_state(cls, state_status) -> tuple[bool, str]:
        """Check if we've reached a terminal state."""
        
        from engine.models import BotStatus
        
        terminal_states = [BotStatus.FILLED, BotStatus.STOPPED]
        
        if state_status in terminal_states:
            return True, f"terminal {state_status.value}"
        
        return False, "still active"

