"""
Tests for engine/models.py - Pydantic data models validation.
"""

import pytest


class TestBotConfig:
    """Test cases for BotConfig model."""
    
    def test_valid_bot_creation(self, sample_bot_config):
        """Verify valid bot configuration is created correctly."""
        assert sample_bot_config.bot_id is not None
        assert sample_bot_config.coin == "BTC"
        assert sample_bot_config.trail_type.value == "long_entry"
        assert sample_bot_config.size_usd == 100.0
        assert sample_bot_config.offset_pct == 0.8
        assert sample_bot_config.max_chase_pct == 1.5
    
    def test_invalid_min_size_validation(self):
        """Test that sizes below $50 are rejected."""
        from engine.models import BotConfig, TrailType
        
        with pytest.raises(ValueError) as exc_info:
            BotConfig(
                bot_id="test",
                coin="ETH",
                trail_type=TrailType.LONG_ENTRY,
                size_usd=10.0,  # Too small
                offset_pct=0.5,
                max_chase_pct=1.0
            )
        
        assert "Minimum size is" in str(exc_info.value)
    
    def test_invalid_percentage_validation(self):
        """Test percentage range validation."""
        from engine.models import BotConfig, TrailType
        
        with pytest.raises(ValueError):
            BotConfig(
                bot_id="test",
                coin="ETH",
                trail_type=TrailType.LONG_ENTRY,
                size_usd=100.0,
                offset_pct=0.05,  # Below min
                max_chase_pct=1.0
            )
    
    def test_max_must_exceed_offset(self):
        """Verify max_chase_pct must be greater than offset."""
        from engine.models import BotConfig, TrailType
        
        with pytest.raises(ValueError) as exc_info:
            BotConfig(
                bot_id="test",
                coin="BTC",
                trail_type=TrailType.SHORT_ENTRY,
                size_usd=100.0,
                offset_pct=1.5,
                max_chase_pct=1.0  # Less than offset
            )
        
        assert "max_chase_pct must be greater than offset_pct" in str(exc_info.value)
    
    def test_coin_uppercase_normalization(self):
        """Test coin ticker normalization."""
        from engine.models import BotConfig, TrailType
        
        config = BotConfig(
            bot_id="test",
            coin="eth",  # lowercase
            trail_type=TrailType.SHORT_EXIT,
            size_usd=200.0,
            offset_pct=1.0,
            max_chase_pct=2.0
        )
        
        assert config.coin == "ETH"
    
    def test_get_side_returns_correct_direction(self):
        """Test side determination from trail type."""
        from engine.models import BotConfig, TrailType
        
        test_cases = [
            (TrailType.LONG_ENTRY, "BUY"),
            (TrailType.SHORT_ENTRY, "SELL"),
            (TrailType.LONG_EXIT, "SELL"),
            (TrailType.SHORT_EXIT, "BUY")
        ]
        
        for trail_type, expected_side in test_cases:
            config = BotConfig(
                bot_id=f"test-{trail_type.value}",
                coin="BTC",
                trail_type=trail_type,
                size_usd=100.0,
                offset_pct=0.8,
                max_chase_pct=1.5,
            )
            assert config.get_side() == expected_side


class TestBotState:
    """Test BotState model properties."""
    
    def test_bot_state_initialization(self, sample_bot_state):
        """Verify bot state is properly initialized."""
        assert sample_bot_state.bot_id == "test-bot-001"
        assert sample_bot_state.status.value == "trailing"
        assert sample_bot_state.oid == 12345
    
    def test_display_limit_price_formatting(self, sample_bot_state):
        """Test limit price display formatting."""
        formatted = f"${sample_bot_state.current_limit_price:,.2f}"
        assert formatted == "$67,850.00"


class ValidationErrorsTestCase:
    """Test ValidationErrors utility model."""
    
    def test_validation_errors_empty_initialization(self):
        from engine.models import ValidationErrors
        
        errors = ValidationErrors()
        assert len(errors.errors) == 0
    
    def test_add_single_error(self):
        from engine.models import ValidationErrors
        
        errors = ValidationErrors()
        errors.add("Test error message")
        assert len(errors.errors) == 1
        assert errors.errors[0] == "Test error message"
    
    def test_extend_multiple_errors(self):
        from engine.models import ValidationErrors
        
        errors = ValidationErrors()
        errors.extend(["Error 1", "Error 2"])
        
        assert len(errors.errors) == 2
        assert errors.errors[0] == "Error 1"
        assert errors.errors[1] == "Error 2"
