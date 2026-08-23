"""
Configuration loader for HyperTrail application.
Handles environment variables and configuration validation.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Constants are imported directly, not via relative import
from constants import NETWORK_MODE, API_ENDPOINTS

# Load .env file from project root
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    def __init__(self):
        # API credentials (loaded from .env or required for operation)
        self.HYPERLIQUID_ACCOUNT_ADDRESS = os.getenv(
            "HYPERLIQUID_ACCOUNT_ADDRESS", 
            ""
        )
        
        # Network-specific secret key selection
        self.NETWORK_MODE: str = os.getenv(
            "HYPERLIQUID_NETWORK",
            NETWORK_MODE.value
        ).lower()
        
        # Load the appropriate secret key based on network mode
        if self.NETWORK_MODE == "mainnet":
            self.HYPERLIQUID_SECRET_KEY = os.getenv(
                "HYPERLIQUID_MAINNET_SECRET_KEY",
                ""
            )
        else:  # default to testnet
            self.HYPERLIQUID_SECRET_KEY = os.getenv(
                "HYPERLIQUID_TESTNET_SECRET_KEY",
                ""
            )
        
        # Network endpoint selection
        if self.NETWORK_MODE == "mainnet":
            self.API_URL = API_ENDPOINTS["mainnet"]
        else:  # default to testnet
            self.API_URL = API_ENDPOINTS["testnet"]
        
        # Runtime parameters
        self.WEB_SOCKET_ENABLED: bool = True
    
    def validate_required_fields(self) -> list[str]:
        """Validate configuration. Returns list of error messages (empty if valid)."""
        errors = []
        
        if not self.HYPERLIQUID_ACCOUNT_ADDRESS:
            errors.append("HYPERLIQUID_ACCOUNT_ADDRESS is not set in .env file")
        
        if not self.HYPERLIQUID_SECRET_KEY:
            secret_key_var = "HYPERLIQUID_MAINNET_SECRET_KEY" if self.NETWORK_MODE == "mainnet" else "HYPERLIQUID_TESTNET_SECRET_KEY"
            errors.append(f"{secret_key_var} is not set in .env file (network mode: {self.NETWORK_MODE})")
        
        return errors
    
    def is_valid(self) -> bool:
        """Return True if all required fields are configured."""
        return len(self.validate_required_fields()) == 0


# Global config singleton instance
config = Config()
