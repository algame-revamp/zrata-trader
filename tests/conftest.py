"""
Global pytest configuration and fixtures.

This file is automatically loaded by pytest and contains:
- Shared fixtures used across multiple test files
- Test configuration
- Common test utilities
"""

import os
import tempfile
from typing import Any, Dict

import pytest


@pytest.fixture
def sample_csv_data() -> bytes:
    """
    Fixture that provides sample CSV data for testing.
    
    This is a 'fixture' - a reusable test component that sets up
    data or conditions needed by multiple tests.
    """
    csv_content = """Date,Open,High,Low,Close,Volume
2023-01-01,100.0,102.0,99.0,101.0,10000
2023-01-02,101.0,103.5,100.5,102.5,11000
2023-01-03,102.5,104.0,101.0,103.0,9500
2023-01-04,103.0,105.0,102.0,104.5,12000
2023-01-05,104.5,106.0,103.5,105.0,10500"""
    
    return csv_content.encode('utf-8')

@pytest.fixture
def sample_csv_data_modified() -> bytes:
    """
    Fixture with slightly modified CSV data (should produce different hash).
    """
    csv_content = """Date,Open,High,Low,Close,Volume
2023-01-01,100.0,102.0,99.0,101.0,10000
2023-01-02,101.0,103.5,100.5,102.5,11000
2023-01-03,102.5,104.0,101.0,103.0,9500
2023-01-04,103.0,105.0,102.0,104.5,12000
2023-01-05,104.5,106.0,103.5,105.1,10500"""  # Changed 105.0 to 105.1
    
    return csv_content.encode('utf-8')

@pytest.fixture
def sample_strategy_config() -> Dict[str, Any]:
    """Sample strategy configuration for testing."""
    return {
        "type": "sma_cross",
        "fast": 10,
        "slow": 20,
        "parameters": {
            "exit_strategy": "stop_loss",
            "stop_loss_pct": 0.05
        }
    }

@pytest.fixture  
def sample_backtest_params() -> Dict[str, Any]:
    """Sample backtest parameters for testing."""
    return {
        "initial_capital": 10000.0,
        "commission": 0.002,
        "slippage": 0.001
    }

@pytest.fixture
def temp_db_file():
    """
    Fixture that creates a temporary database file for testing.
    
    This demonstrates how to create temporary resources for tests
    that are automatically cleaned up.
    """
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_file.close()
    
    yield temp_file.name  # This is what gets passed to test functions
    
    # Cleanup after test
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)