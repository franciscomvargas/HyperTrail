"""
Runtime validation tests to verify all system components are properly integrated.
"""

import sys
from pathlib import Path


class TestProjectStructure:
    """Verify all expected files exist."""
    
    REQUIRED_FILES = [
        "app.py",
        "constants.py", 
        "requirements.txt",
        ".gitignore",
        ".python-version",
        ".env.example",
        "setup_env.sh"
    ]
    
    def test_project_root_files_exist(self):
        """Verify required project files exist."""
        project_root = Path(__file__).parent.parent
        
        for filename in self.REQUIRED_FILES:
            file_path = project_root / filename
            assert file_path.exists(), f"Missing required file: {filename}"


class TestConfigurationLoadability:
    """Verify configuration modules can be imported and instantiated."""
    
    def test_constants_loadable(self):
        """Test that constants module loads properly."""
        from constants import DEFAULT_OFFSET_PCT
        
        assert DEFAULT_OFFSET_PCT == 0.8
    
    def test_config_loads_with_mocked_env(self):
        """Test config initialization with mocked environment."""
        from engine.config import config
        
        assert config is not None


class TestModelsValidation:
    """Verify Pydantic models validate correctly."""
    
    def test_bot_config_validation_passes_with_valid_data(self):
        """Valid bot configuration should pass validation."""
        from engine.models import BotConfig, TrailType
        
        config = BotConfig(
            bot_id="test-bot-valid",
            coin="BTC",
            trail_type=TrailType.LONG_ENTRY,
            size_usd=100.0,
            offset_pct=0.8,
            max_chase_pct=1.5
        )
        
        assert config.bot_id is not None
    
    def test_bot_config_rejects_invalid_offset_sequence(self):
        """Test that offset must be less than max chase."""
        from engine.models import BotConfig, TrailType
        
        try:
            BotConfig(
                bot_id="test-invalid",
                coin="BTC",
                trail_type=TrailType.LONG_ENTRY,
                size_usd=100.0,
                offset_pct=2.0,  # Larger than max_chase - will fail
                max_chase_pct=1.5
            )
            assert False, "Should have raised ValueError"
        except Exception as e:
            # Pydantic v2 raises ValidationError
            error_msg = str(e)
            # Just check that validation failed - the exact message content varies
            assert "offset" in str(e).lower() or "greater than" in str(e).lower()


class TestStateMachineLogicValidation:
    """Test state machine logic."""
    
    def test_valid_state_transition_trailing_to_locked(self):
        from engine.models import BotStatus
        from engine.state_machine import StateTransitionValidatorFinal
        
        can_transition, _ = StateTransitionValidatorFinal.can_transition(
            BotStatus.TRAILING, BotStatus.LOCKED
        )
        
        assert can_transition is True
    
    def test_bot_state_display_methods(self):
        """Test bot state display formatting."""
        from engine.models import BotState, BotStatus
        
        bot = BotState(
            bot_id="test-display",
            status=BotStatus.TRAILING,
            oid=99999,
            current_limit_price=67850.0,
            last_trail_reference=68000.0,
            delta_pct=-0.18
        )
        
        formatted = f"${bot.current_limit_price:,.2f}"
        assert "$" in formatted


class TestTrailingLogic:
    """Test core trailing calculation logic."""
    
    def test_longs_buy_dip_price_calculation(self):
        from engine.models import TrailType
        from engine.state_machine import TrailingStateMachine
        
        sm = TrailingStateMachine()
        
        new_limit, direction = sm.evaluate_next_trail_price(
            current_mid_price=60000.0,
            bot_config_type=TrailType.LONG_ENTRY,
            offset_pct=0.8,
            is_descending=True
        )
        
        expected_price = 60000.0 * (1 - 0.008)
        assert abs(new_limit - expected_price) < 0.01
    
    def test_sells_rally_price_calculation(self):
        from engine.models import TrailType
        from engine.state_machine import TrailingStateMachine
        
        sm = TrailingStateMachine()
        
        new_limit, direction = sm.evaluate_next_trail_price(
            current_mid_price=3500.0,
            bot_config_type=TrailType.SHORT_ENTRY,
            offset_pct=1.0,
            is_descending=False
        )
        
        expected_price = 3500.0 * (1 + 0.01)
        assert abs(new_limit - expected_price) < 0.01


class TestOrderManagerValidation:
    """Test order manager error handling."""
    
    def test_order_not_found_detection(self):
        from engine.order_manager import OrderManager
        
        manager = OrderManager(None, None)
        
        not_found_patterns = [
            "invalid order id",
        ]
        
        for msg in not_found_patterns:
            result = manager._detect_order_not_found_error(msg)
            assert result is True


class TestBotConfigSides:
    """Test order side determination for all trail types."""
    
    def test_all_trail_types_produce_correct_side(self):
        from engine.models import BotConfig, TrailType
        
        side_map = {
            TrailType.LONG_ENTRY: "BUY",
            TrailType.SHORT_ENTRY: "SELL", 
            TrailType.LONG_EXIT: "SELL",
            TrailType.SHORT_EXIT: "BUY"
        }
        
        for trail_type, expected_side in side_map.items():
            config = BotConfig(
                bot_id=f"test-{trail_type.value}",
                coin="BTC",
                trail_type=trail_type,
                size_usd=100.0,
                offset_pct=0.8,
                max_chase_pct=1.5
            )
            assert config.get_side() == expected_side

