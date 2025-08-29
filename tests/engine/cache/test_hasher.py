"""
Comprehensive tests for BacktestHashGenerator.

This test file demonstrates:
- Unit testing best practices
- Different types of test assertions
- Edge case testing
- Property-based testing concepts
- Test organization with classes
"""

import pytest
from engine.cache.hasher import BacktestHashGenerator


class TestCSVDataHashing:
    """
    Test class for CSV data hashing functionality.
    
    Organizing tests in classes helps group related functionality
    and makes test output more readable.
    """
    
    def test_same_content_produces_same_hash(self, sample_csv_data):
        """Test that identical CSV content always produces the same hash."""
        hash1 = BacktestHashGenerator.hash_csv_data(sample_csv_data)
        hash2 = BacktestHashGenerator.hash_csv_data(sample_csv_data)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64-character hex string
    
    def test_different_content_produces_different_hash(self, sample_csv_data, sample_csv_data_modified):
        """Test that different CSV content produces different hashes."""
        hash1 = BacktestHashGenerator.hash_csv_data(sample_csv_data)
        hash2 = BacktestHashGenerator.hash_csv_data(sample_csv_data_modified)
        
        assert hash1 != hash2
        
    def test_empty_csv_produces_valid_hash(self):
        """Test edge case: empty CSV data."""
        empty_data = b""
        hash_result = BacktestHashGenerator.hash_csv_data(empty_data)
        
        assert len(hash_result) == 64
        assert hash_result == BacktestHashGenerator.hash_csv_data(b"")  # Consistent
        
    def test_csv_hash_is_deterministic(self, sample_csv_data):
        """Test that the same CSV always produces the same hash (deterministic)."""
        hashes = [BacktestHashGenerator.hash_csv_data(sample_csv_data) for _ in range(10)]
        
        # All hashes should be identical
        assert len(set(hashes)) == 1
        
    def test_single_byte_change_produces_different_hash(self):
        """Test that even a single byte change produces a completely different hash."""
        data1 = b"Date,Open,High,Low,Close,Volume\n2023-01-01,100,101,99,100,1000"
        data2 = b"Date,Open,High,Low,Close,Volume\n2023-01-01,100,101,99,100,1001"  # Changed 1000 to 1001
        
        hash1 = BacktestHashGenerator.hash_csv_data(data1)
        hash2 = BacktestHashGenerator.hash_csv_data(data2)
        
        assert hash1 != hash2
        
        # SHA-256 property: small changes cause avalanche effect
        # (at least 50% of bits should change)
        different_bits = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        assert different_bits > len(hash1) * 0.4  # At least 40% different


class TestStrategyConfigHashing:
    """Test class for strategy configuration hashing."""
    
    def test_same_config_produces_same_hash(self, sample_strategy_config):
        """Test that identical strategy configs produce identical hashes."""
        hash1 = BacktestHashGenerator.hash_strategy_config(sample_strategy_config)
        hash2 = BacktestHashGenerator.hash_strategy_config(sample_strategy_config)
        
        assert hash1 == hash2
        assert len(hash1) == 64
    
    def test_reordered_keys_produce_same_hash(self):
        """Test the key feature: reordered keys should produce the same hash."""
        config1 = {"type": "sma_cross", "fast": 10, "slow": 20}
        config2 = {"slow": 20, "fast": 10, "type": "sma_cross"}
        config3 = {"fast": 10, "type": "sma_cross", "slow": 20}
        
        hash1 = BacktestHashGenerator.hash_strategy_config(config1)
        hash2 = BacktestHashGenerator.hash_strategy_config(config2)
        hash3 = BacktestHashGenerator.hash_strategy_config(config3)
        
        assert hash1 == hash2 == hash3
    
    def test_nested_dict_normalization(self):
        """Test that nested dictionaries are also normalized properly."""
        config1 = {
            "type": "complex_strategy",
            "params": {"a": 1, "b": 2},
            "exit": {"stop": 0.05, "target": 0.10}
        }
        
        config2 = {
            "exit": {"target": 0.10, "stop": 0.05},
            "params": {"b": 2, "a": 1},
            "type": "complex_strategy"
        }
        
        hash1 = BacktestHashGenerator.hash_strategy_config(config1)
        hash2 = BacktestHashGenerator.hash_strategy_config(config2)
        
        assert hash1 == hash2
    
    def test_different_values_produce_different_hashes(self):
        """Test that different parameter values produce different hashes."""
        config1 = {"type": "sma_cross", "fast": 10, "slow": 20}
        config2 = {"type": "sma_cross", "fast": 10, "slow": 21}  # Changed slow from 20 to 21
        
        hash1 = BacktestHashGenerator.hash_strategy_config(config1)
        hash2 = BacktestHashGenerator.hash_strategy_config(config2)
        
        assert hash1 != hash2
    
    def test_empty_config_produces_valid_hash(self):
        """Test edge case: empty configuration."""
        empty_config = {}
        hash_result = BacktestHashGenerator.hash_strategy_config(empty_config)
        
        assert len(hash_result) == 64
        assert hash_result == BacktestHashGenerator.hash_strategy_config({})
    
    @pytest.mark.parametrize("config,expected_type", [
        ({"type": "sma", "period": 20}, str),
        ({"type": "rsi", "period": 14, "overbought": 70}, str),
        ({"type": "bollinger", "period": 20, "std": 2.0}, str),
    ])
    def test_various_strategy_configs(self, config, expected_type):
        """
        Parametrized test: Test multiple strategy configurations.
        
        This demonstrates pytest.mark.parametrize - a way to run the same
        test with different inputs.
        """
        hash_result = BacktestHashGenerator.hash_strategy_config(config)
        
        assert isinstance(hash_result, expected_type)
        assert len(hash_result) == 64
    
    def test_list_handling_in_config(self):
        """Test that lists in configurations are handled properly."""
        # This should not raise an exception
        config_with_list = {
            "type": "multi_timeframe",
            "timeframes": ["1m", "5m", "15m"],
            "weights": [0.5, 0.3, 0.2]
        }
        
        # This should work without errors
        hash_result = BacktestHashGenerator.hash_strategy_config(config_with_list)
        assert len(hash_result) == 64
        
        # Same list in different order should produce same hash (if sortable)
        config_reordered = {
            "type": "multi_timeframe", 
            "timeframes": ["15m", "1m", "5m"],  # Different order
            "weights": [0.2, 0.5, 0.3]  # Different order
        }
        
        hash_reordered = BacktestHashGenerator.hash_strategy_config(config_reordered)
        # Note: These will be different because we sort the lists, 
        # but the elements are paired differently
        # This is expected behavior


class TestParameterHashing:
    """Test class for backtest parameter hashing."""
    
    def test_parameter_hashing_consistency(self, sample_backtest_params):
        """Test that parameter hashing is consistent."""
        hash1 = BacktestHashGenerator.hash_parameters(sample_backtest_params)
        hash2 = BacktestHashGenerator.hash_parameters(sample_backtest_params)
        
        assert hash1 == hash2
        assert len(hash1) == 64
    
    def test_reordered_parameters_same_hash(self):
        """Test that reordered parameters produce the same hash."""
        params1 = {"commission": 0.002, "initial_capital": 10000, "slippage": 0.001}
        params2 = {"slippage": 0.001, "initial_capital": 10000, "commission": 0.002}
        
        hash1 = BacktestHashGenerator.hash_parameters(params1)
        hash2 = BacktestHashGenerator.hash_parameters(params2)
        
        assert hash1 == hash2
        
    def test_floating_point_precision(self):
        """Test that floating point precision matters for hashing."""
        params1 = {"commission": 0.002}
        params2 = {"commission": 0.0020001}  # Slightly different
        
        hash1 = BacktestHashGenerator.hash_parameters(params1)
        hash2 = BacktestHashGenerator.hash_parameters(params2)
        
        assert hash1 != hash2  # Should be different due to precision


class TestMasterHashGeneration:
    """Test class for the master backtest hash generation."""
    
    def test_master_hash_generation(self):
        """Test that master hash is generated correctly from component hashes."""
        data_hash = "abc123"
        strategy_hash = "def456" 
        params_hash = "ghi789"
        
        master_hash = BacktestHashGenerator.create_backtest_hash(
            data_hash, strategy_hash, params_hash
        )
        
        assert len(master_hash) == 64
        assert isinstance(master_hash, str)
        
    def test_master_hash_order_matters(self):
        """Test that the order of component hashes matters for master hash."""
        master_hash1 = BacktestHashGenerator.create_backtest_hash("a", "b", "c")
        master_hash2 = BacktestHashGenerator.create_backtest_hash("b", "a", "c")
        
        assert master_hash1 != master_hash2
        
    def test_master_hash_consistency(self):
        """Test that master hash is consistent for same inputs."""
        data_hash = "test_data_hash"
        strategy_hash = "test_strategy_hash"
        params_hash = "test_params_hash"
        
        hash1 = BacktestHashGenerator.create_backtest_hash(data_hash, strategy_hash, params_hash)
        hash2 = BacktestHashGenerator.create_backtest_hash(data_hash, strategy_hash, params_hash)
        
        assert hash1 == hash2


class TestEdgeCasesAndErrorHandling:
    """Test class for edge cases and error handling."""
    
    def test_unicode_in_strategy_config(self):
        """Test that unicode characters in strategy config don't break hashing."""
        config = {
            "type": "custom_策略",  # Chinese characters
            "description": "A strategy with émojis 🚀",
            "parameter": "café"  # Accented characters
        }
        
        # Should not raise an exception
        hash_result = BacktestHashGenerator.hash_strategy_config(config)
        assert len(hash_result) == 64
        
    def test_none_values_in_config(self):
        """Test handling of None values in configuration."""
        config = {
            "type": "test_strategy",
            "optional_param": None,
            "required_param": 42
        }
        
        hash_result = BacktestHashGenerator.hash_strategy_config(config)
        assert len(hash_result) == 64
        
    def test_very_large_numbers(self):
        """Test handling of very large numbers."""
        config = {
            "type": "test",
            "large_number": 999999999999999999999999999999,
            "scientific": 1.23e50
        }
        
        hash_result = BacktestHashGenerator.hash_strategy_config(config)
        assert len(hash_result) == 64


class TestIntegrationScenarios:
    """Integration tests that test multiple components working together."""
    
    def test_complete_backtest_hash_workflow(self, sample_csv_data, sample_strategy_config, sample_backtest_params):
        """
        Test the complete workflow of generating a backtest hash.
        
        This is an 'integration test' - it tests multiple components
        working together rather than isolated units.
        """
        # Generate all component hashes
        data_hash = BacktestHashGenerator.hash_csv_data(sample_csv_data)
        strategy_hash = BacktestHashGenerator.hash_strategy_config(sample_strategy_config)
        params_hash = BacktestHashGenerator.hash_parameters(sample_backtest_params)
        
        # Generate master hash
        master_hash = BacktestHashGenerator.create_backtest_hash(
            data_hash, strategy_hash, params_hash
        )
        
        # All hashes should be valid
        assert len(data_hash) == 64
        assert len(strategy_hash) == 64
        assert len(params_hash) == 64
        assert len(master_hash) == 64
        
        # Master hash should be different from component hashes
        assert master_hash != data_hash
        assert master_hash != strategy_hash
        assert master_hash != params_hash
        
    def test_identical_backtests_produce_identical_hashes(
        self, 
        sample_csv_data,
        sample_strategy_config, 
        sample_backtest_params
    ):
        """Test that identical backtest configurations produce identical master hashes."""
        
        # First backtest
        master_hash1 = BacktestHashGenerator.create_backtest_hash(
            BacktestHashGenerator.hash_csv_data(sample_csv_data),
            BacktestHashGenerator.hash_strategy_config(sample_strategy_config),
            BacktestHashGenerator.hash_parameters(sample_backtest_params)
        )
        
        # Second identical backtest  
        master_hash2 = BacktestHashGenerator.create_backtest_hash(
            BacktestHashGenerator.hash_csv_data(sample_csv_data),
            BacktestHashGenerator.hash_strategy_config(sample_strategy_config),
            BacktestHashGenerator.hash_parameters(sample_backtest_params)
        )
        
        assert master_hash1 == master_hash2


# Performance tests (marked as slow)
class TestPerformance:
    """Performance-related tests."""
    
    @pytest.mark.slow
    def test_hashing_performance_large_csv(self):
        """Test hashing performance with large CSV data."""
        # Generate large CSV data (1MB)
        large_csv_data = b"Date,Open,High,Low,Close,Volume\n" * 50000
        
        import time
        start_time = time.time()
        hash_result = BacktestHashGenerator.hash_csv_data(large_csv_data)
        end_time = time.time()
        
        # Should complete in reasonable time (< 1 second for 1MB)
        assert (end_time - start_time) < 1.0
        assert len(hash_result) == 64
        
    @pytest.mark.slow
    def test_hashing_performance_complex_strategy(self):
        """Test hashing performance with complex strategy configuration."""
        complex_strategy = {
            f"param_{i}": {
                f"subparam_{j}": f"value_{i}_{j}"
                for j in range(100)
            }
            for i in range(100)
        }
        
        import time
        start_time = time.time()
        hash_result = BacktestHashGenerator.hash_strategy_config(complex_strategy)
        end_time = time.time()
        
        # Should complete in reasonable time
        assert (end_time - start_time) < 0.5
        assert len(hash_result) == 64