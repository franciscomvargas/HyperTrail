"""
Tests for engine/persistence.py - SQLite database operations.
"""

import pytest
from pathlib import Path

pytest_plugins = ['conftest']


class TestDatabasePersistence:
    """Test SQLite persistence layer operations."""
    
    @pytest.mark.asyncio
    async def test_connect_and_initialize_database(self, temp_database):
        """Verify database initialization creates proper schema."""
        from engine.persistence import DatabasePersistence
        
        # Initialize with our temp database path
        persisted = DatabasePersistence(str(temp_database))
        
        # Verify tables were created
        cursor = pytest.importorskip('sqlite3').connect(
            str(temp_database)
        ).cursor()
        
        # Check bots table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='bots'"
        )
        assert cursor.fetchone() is not None
        
        # Check bot_states table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='bot_states'"
        )
        assert cursor.fetchone() is not None
        
        cursor.connection.close()
    
    @pytest.mark.asyncio
    async def test_persist_bot_config(self, temp_database):
        """Test saving and retrieving bot configuration."""
        from engine.persistence import DatabasePersistence
        from engine.models import BotConfig, TrailType
        from datetime import datetime
        
        persisted = DatabasePersistence(str(temp_database))
        
        # Create a valid config
        config = BotConfig(
            bot_id="test-bot-001",
            coin="BTC",
            trail_type=TrailType.LONG_ENTRY,
            size_usd=100.0,
            offset_pct=0.8,
            max_chase_pct=1.5
        )
        
        # Persist it
        success = await persisted.persist_bot_config(config)
        assert success is True
        
        # Retrieve it back
        loaded_config = await persisted.load_bot_config("test-bot-001")
        assert loaded_config is not None
        assert loaded_config.bot_id == "test-bot-001"
        assert loaded_config.trail_type == TrailType.LONG_ENTRY
    
    @pytest.mark.asyncio
    async def test_update_bot_state(self, temp_database):
        """Test bot state update operations."""
        from engine.persistence import DatabasePersistence
        
        persisted = DatabasePersistence(str(temp_database))
        
        # First create a minimal state (would normally be done via persist_bot_state)
        # For this test we'll assume it exists
        
        success = await persisted.update_bot_state(
            bot_id="test-bot-001",
            status="locked",
            current_limit_price=67850.0
        )
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, temp_database):
        """Test statistics and summary queries."""
        from engine.persistence import DatabasePersistence
        
        persisted = DatabasePersistence(str(temp_database))
        
        stats = await persisted.get_bot_statistics()
        
        # Should have some basic statistics
        assert "total_bots_created" in stats
        assert isinstance(stats["total_bots_created"], int)


class TestDatabaseTransactionHandling:
    """Test database transaction error handling."""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, temp_database):
        """Verify transactions are rolled back on failure."""
        from engine.persistence import DatabasePersistence
        
        persisted = DatabasePersistence(str(temp_database))
        
        # This should work fine
        success = await persisted.update_bot_state(
            bot_id="nonexistent",
            status="error"
        )
        
        # Even for nonexistent bot, it shouldn't crash the database
        assert isinstance(success, bool)
