"""
Pytest configuration and shared fixtures for HyperTrail test suite.
Provides common test infrastructure for all engine components.
"""

import pytest
import asyncio
from pathlib import Path
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load test environment variables
load_dotenv("tests/.env.test", override=True)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy for pytest-asyncio."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(autouse=True)
def mock_environment_variables():
    """Mock API credentials to prevent actual network calls in tests."""
    with patch.dict(os.environ, {
        "HYPERLIQUID_ACCOUNT_ADDRESS": "TEST_ADDR_1234567890ABCDEF",
        "HYPERLIQUID_SECRET_KEY": "test_secret_key_for_testing_purposes_only",
        "HYPERLIQUID_NETWORK": "testnet"
    }):
        yield


@pytest.fixture
def sample_bot_config():
    """Provide a valid sample BotConfig for testing."""
    from engine.models import BotConfig, TrailType
    
    return BotConfig(
        bot_id="test-bot-001",
        coin="BTC",
        trail_type=TrailType.LONG_ENTRY,
        size_usd=100.0,
        offset_pct=0.8,
        max_chase_pct=1.5,
    )


@pytest.fixture
def sample_bot_state(sample_bot_config):
    """Provide a valid sample BotState for testing."""
    from engine.models import BotState, BotStatus
    
    return BotState(
        bot_id=sample_bot_config.bot_id,
        status=BotStatus.TRAILING,
        oid=12345,
        current_limit_price=67850.0,
        last_trail_reference=68000.0,
        delta_pct=-0.18
    )


@pytest.fixture
def sample_market_snapshot():
    """Provide a sample L2 market snapshot."""
    from datetime import datetime
    
    return {
        "coin": "BTC",
        "current_price": 67900.0,
        "best_bid": 67895.0,
        "best_ask": 67905.0,
        "spread_pct": 0.0147,
        "timestamp": datetime.now()
    }


@pytest.fixture
def mock_exchange():
    """Mock hyperliquid exchange object."""
    exchange = MagicMock(spec=MagicMock)
    
    # Mock methods that would be called during order operations
    exchange.order = AsyncMock(return_value={
        "status": "ok",
        "response": {
            "data": {
                "statuses": [{"resting": {"oid": 98765}}]
            }
        }
    })
    
    exchange.modify_order = AsyncMock(return_value={
        "status": "ok",
        "response": {
            "data": {
                "statuses": [{"modified": {"oid": 98765}}]
            }
        }
    })
    
    exchange.modify_orders = AsyncMock(return_value={
        "status": "ok",
        "response": {
            "data": {
                "statuses": [
                    {"modified": {"oid": 123}},
                    {"not_modified": {"aid": 456}}
                ]
            }
        }
    })
    
    exchange.cancel = AsyncMock(return_value={
        "status": "ok"
    })
    
    return exchange


@pytest.fixture
def mock_info():
    """Mock hyperliquid info object."""
    info = MagicMock(spec=MagicMock)
    info.query_order_by_oid = AsyncMock(return_value={
        "status": "ok",
        "response": {
            "order": {
                "oid": 12345,
                "status": {"resting": True}
            }
        }
    })
    return info


@pytest.fixture
def temp_database(tmp_path):
    """Provide temporary database file for persistence tests."""
    db_path = tmp_path / "test_bots.db"
    os.environ["HYPERTRAIL_DB_PATH"] = str(db_path)
    return db_path

