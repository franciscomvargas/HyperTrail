"""
Smoke tests for HyperTrail TUI application interface readiness.
These tests verify that key components can be imported and instantiated correctly,
ensuring we won't encounter runtime crashes when launching the live interface.
"""

import pytest
from inspect import isclass


class TestImportReadiness:
    """Verify all critical modules can be imported without errors."""
    
    def test_engine_models_importable(self):
        """Core data models should import successfully."""
        from engine.models import BotConfig, BotState, TrailType, BotStatus
        assert BotConfig is not None
    
    def test_state_machine_importable(self):
        """State machine logic should be accessible."""
        from engine.state_machine import TrailingStateMachine
        assert TrailingStateMachine is not None
    
    def test_order_manager_importable(self):
        """Order management utilities should load."""
        from engine.order_manager import OrderManager
        assert OrderManager is not None
    
    def test_persistence_available(self):
        """Database persistence layer should be functional."""
        from engine.persistence import DatabasePersistence
        assert DatabasePersistence is not None


class TestConfigurationLoading:
    """Verify configuration loads correctly with actual .env values."""
    
    def test_config_instance_created(self):
        """Config singleton should initialize properly."""
        from engine.config import config
        assert config is not None
    
    def test_network_selection_available(self):
        """Network configuration constants available."""
        from constants import NETWORK_MODE
        assert hasattr(NETWORK_MODE, "value")
    
    @pytest.mark.skip(reason="Live API credentials not configured for testing")
    def test_api_credentials_present(self):
        """API credentials should be configured for live testing."""
        from engine.config import config
        errors = config.validate_required_fields()
        if not config.is_valid():
            pytest.fail(f"Configuration validation failed: {errors}")


class TestTUIComponentImport:
    """Verify TUI components can be loaded without crashes."""
    
    def test_textual_app_file_exists(self):
        """Textual app module should exist."""
        import os
        assert os.path.exists("app.py"), "app.py not found!"
    
    def test_textual_framework_available(self):
        """Textual framework requirements met."""
        import textual
        assert textual.__version__ >= "0.45.0"


class TestCoreFunctionalityValidation:
    """Validate core trailing logic functions without mocking."""
    
    def test_trailing_state_machine_initializes(self):
        """Trailing state machine should instantiate with defaults."""
        from engine.state_machine import TrailingStateMachine
        
        state_machine = TrailingStateMachine()
        assert isinstance(state_machine, TrailingStateMachine)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
