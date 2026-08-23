"""
Constants configuration for HyperTrail Trailing Order Management System.
Network settings, safety thresholds, and default parameters.
"""

from enum import Enum

# Network Configuration
class NetworkMode(str, Enum):
    TESTNET = "testnet"
    MAINNET = "mainnet"

# Default network (safe to test without real money)
NETWORK_MODE: NetworkMode = NetworkMode.TESTNET

# API endpoints for different networks
API_ENDPOINTS = {
    NetworkMode.TESTNET: "https://api.hyperliquid-prod.com/sandbox",
    NetworkMode.MAINNET: "https://api.hyperliquid.xyz",
}

# WebSocket L2 Book subscription details
L2_BOOK_UPDATE_INTERVAL_MS = 100  # Polling frequency for state updates

# Default trailing parameters (user-configurable via UI)
DEFAULT_OFFSET_PCT = 0.8       # Initial trailing distance percentage
DEFAULT_MAX_CHASE_PCT = 1.5    # Circuit breaker threshold
MIN_ALLOWED_OFFSET_PCT = 0.1   # Minimum valid offset (0.1%)
MAX_ALLOWED_OFFSET_PCT = 5.0   # Maximum valid offset (5.0%)

# Safety circuit parameters
REVERSAL_THRESHOLD_PCT = 0.3   # Price bounce threshold to trigger lock
MIN_SPREAD_PCT = 0.1           # Minimum allowed order spread during high vol
MAX_MARGIN_UTILIZATION_PCT = 30.0  # Single order should not exceed this

# Retry configuration for API operations
MAX_ORDER_RETRIES = 3
RETRY_BACKOFF_MS = [1000, 3000, 5000]  # Exponential backoff for retries

# Time settings for bot state tracking
BOT_STATE_POLLING_INTERVAL_MS = 250  # How often to poll bot state (for persisted bots)
KEEPALIVE_PING_SECONDS = 10          # WebSocket ping/keepalive interval

# Order sizing constraints
MIN_ORDER_SIZE_USD = 50.0            # Minimum order size in USD
MAX_ORDER_SIZE_PCT_OF_MARGIN = 75.0  # Maximum percentage of margin for single order

# Database configuration
DATABASE_NAME = "hypertrail_bots.db"
LOGS_DIR = "logs"

