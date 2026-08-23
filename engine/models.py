"""
Pydantic v2 data models for HyperTrail Trailing Order Management.
Provides type-safe structures for bot configurations, states, and account data.
"""

from typing import Optional, Dict, Any
from uuid import uuid4
from enum import Enum
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, Field, field_validator, model_validator


class TrailType(str, Enum):
    """Types of trailing order strategies."""
    
    LONG_ENTRY = "long_entry"        # Buy dip: descend as price falls, lock on bounce up
    SHORT_ENTRY = "short_entry"      # Sell rally: ascend as price rises, lock on bounce down  
    LONG_EXIT = "long_exit"          # Take profit: trail upward behind long position
    SHORT_EXIT = "short_exit"        # Dip buy: trail downward then up (exit short)


class BotStatus(str, Enum):
    """Lifecycle states for trailing bots."""
    
    INITIALIZING = "initializing"     # Setting up WebSocket sync and initial order
    TRAILING = "trailing"             # Actively updating limit price based on market
    LOCKED = "locked"                 # Price reversed, limit static waiting for cross
    WAITING_FILL = "waiting_fill"     # Resting limit order awaiting fill
    FILLED = "filled"                 # Order executed successfully
    STOPPED = "stopped"               # User halted or circuit breaker triggered
    ERROR = "error"                   # External error requiring manual intervention


class BotConfig(BaseModel):
    """Configuration for a new trailing order bot."""
    
    bot_id: str = Field(default_factory=lambda: str(uuid4()))
    coin: str                           # e.g., "BTC", "ETH", "SOL" (ticker format)
    trail_type: TrailType               # Strategy type
    size_usd: float                     # Order size in USD equivalent
    size_asset: Optional[float] = None         # Optional asset quantity (auto-computed if needed)
    offset_pct: float                   # Initial trailing distance percentage (0.1-5.0)
    max_chase_pct: float                # Safety circuit breaker threshold (> offset)
    reduce_only: bool = False           # Mark order as reduce-only (for exits)
    is_active: bool = True              # Current operational status
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    
    @field_validator('coin')
    @classmethod
    def validate_coin(cls, v: str) -> str:
        """Validate coin ticker format (must be uppercase)."""
        return v.upper()
    
    @field_validator('size_usd')
    @classmethod
    def validate_size_usd(cls, v: float) -> float:
        """Ensure minimum order size."""
        if v < 50.0:
            raise ValueError(f"Minimum size is $50 USD, got {v}")
        return v
    
    @field_validator('offset_pct', 'max_chase_pct')
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Validate percentage range."""
        if not (0.1 <= v <= 5.0):
            raise ValueError("Percentage must be between 0.1% and 5.0%")
        return v
    
    @model_validator(mode='after')
    def validate_safety(self) -> 'BotConfig':
        """Enforce safety circuit: max chase must be > offset."""
        if self.max_chase_pct <= self.offset_pct:
            raise ValueError(
                f"max_chase_pct ({self.max_chase_pct}) must be greater than "
                f"offset_pct ({self.offset_pct})"
            )
        return self
    
    def get_side(self) -> str:
        """Return BUY or SELL based on trail type."""
        return {
            TrailType.LONG_ENTRY: "BUY",
            TrailType.SHORT_ENTRY: "SELL",
            TrailType.LONG_EXIT: "SELL",
            TrailType.SHORT_EXIT: "BUY",
        }[self.trail_type]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding None values)."""
        return {
            'bot_id': self.bot_id,
            'coin': self.coin,
            'trail_type': self.trail_type.value,
            'size_usd': self.size_usd,
            'size_asset': self.size_asset,
            'offset_pct': self.offset_pct,
            'max_chase_pct': self.max_chase_pct,
            'reduce_only': self.reduce_only,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_modified': self.last_modified.isoformat()
        }


class BotState(BaseModel):
    """Current runtime state of an active trailing bot."""
    
    bot_id: str
    status: BotStatus
    oid: Optional[int] = None           # Hyperliquid order ID after placement
    current_limit_price: float = 0.0     # Current limit price (trailing or locked)
    last_trail_reference: float = 0.0    # Reference price for trail calculation
    delta_pct: float = 0.0               # Distance from market price (%)
    
    # Metrics & tracking
    times_active_minutes: int = 0
    fills_count: int = 0
    total_pnli_usd: float = 0.0
    
    # Configuration snapshot (for state persistence)
    config_snapshot: Optional[BotConfig] = None
    
    @property
    def display_limit_price(self) -> str:
        """Formatted limit price."""
        return f"${self.current_limit_price:,.2f}" if self.current_limit_price > 0 else "N/A"
    
    @property
    def delta_display(self) -> str:
        """Formatted delta percentage with direction indicator."""
        sign = "+" if self.delta_pct >= 0 else ""
        return f"{sign}{self.delta_pct:+.2f}%"


class MarketSnapshot(BaseModel):
    """L2 order book snapshot for a specific coin."""
    
    coin: str
    current_price: float
    best_bid: float
    best_ask: float
    mid_price: float
    spread_pct: float      # (ask - bid) / mid * 100
    timestamp: datetime
    
    @field_validator('spread_pct')
    @classmethod
    def calculate_spread(cls, v: float) -> float:
        """Validate spread calculation."""
        if v < 0.0 or v > 100.0:
            raise ValueError(f"Spread percentage out of range: {v}")
        return v


class AccountState(BaseModel):
    """Account summary and connection status."""
    
    address: str                    # Public key (truncated for UI)
    full_address: Optional[str] = None  # Full address if available internally
    cross_margin_usd: float         # Available cross margin in USDC
    account_value_usd: float        # Total account value + P&L
    positions_count: int            # Number of open positions
    
    # Connection status
    connection_status: str = "disconnected"  # connected/reconnecting/disconnected
    last_heartbeat_at: Optional[datetime] = None
    ws_connected_timestamp: Optional[datetime] = None
    
    @property
    def truncated_address(self) -> str:
        """Return first 4 and last 4 characters of address for display."""
        if not self.address or len(self.address) < 8:
            return self.address
        
        return f"{self.address[:4]}...{self.address[-4:]}"


# Utility types for validation errors
class ValidationErrors(BaseModel):
    """Container for validation error messages."""
    errors: list[str] = []
    
    def add(self, error: str) -> None:
        """Add a single error."""
        self.errors.append(error)
    
    def extend(self, errors: list[str]) -> 'ValidationErrors':
        """Extend with multiple errors."""
        self.errors.extend(errors)
        return self
