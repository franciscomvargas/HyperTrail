"""
HyperTrail Core Engine - Trailing Order State Machine & Management
Provides atomic order modifications, state management, and WebSocket integration.

Modules available:
- config: Application configuration loader
- models: Pydantic data structures for bot configurations and states  
- websocket_client: L2 WebSocket market data integration
- order_manager: Atomic order modification operations
- state_machine: Trailing logic engine
- persistence: SQLite database persistence layer
"""

# Do NOT import modules at package level to avoid circular import issues
# Users should explicitly import what they need:
# from engine.models import BotConfig, BotState
# from engine.config import config
# etc.
