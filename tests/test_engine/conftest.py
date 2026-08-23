"""
Per-directory pytest configuration for test_engine sub-suite.
Imports shared fixtures from parent conftest.py.
"""

# Import all fixtures from parent conftest automatically
import sys
from pathlib import Path

# Add parent directory to path to load shared conftest
parent_conftest = Path(__file__).parent.parent / "conftest.py"
if parent_conftest.exists():
    # pytest automatically discovers and loads this as the conftest
    pass
