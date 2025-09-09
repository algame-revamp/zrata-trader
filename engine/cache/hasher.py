import hashlib
import json
from typing import Any, Dict


class BacktestHashGenerator:
    """    
    This class creates unique, consistent hashes for:
    1. CSV data (based on actual content, not filename)
    2. Strategy configurations (JSON objects)
    3. Backtest parameters (commission, initial capital, etc.)
    4. Combined backtest hash (the master key)
    """
    
    @staticmethod
    def hash_csv_data(csv_content: bytes) -> str:
        """
        So we create a unique hash for CSV data based on CONTENT, not filename.

        Why this matters:
        - Two users upload same data with different names → Same hash , so we use the same Backtest Result we had cached
        - Same user uploads same data twice → Same hash , so we avoid redundant processing again
        - Data changes even slightly → Different hash , and we run Backtest again ( maybe we can find ways to make it better later)
        
        Args:
            csv_content: Raw bytes of the CSV file
            
        Returns:
            str: SHA-256 hash of the CSV content
        """
        return hashlib.sha256(csv_content).hexdigest()
    
    @staticmethod
    def hash_strategy_config(strategy_config: Dict[str, Any]) -> str:
        """
        Create a unique hash for strategy configuration JSON ( which we will use in UI to define a strategy defined by user).
        
                
        Here's a interesting thing: JSON objects can be ordered differently but mean the same thing, like eg: 
        {"fast": 10, "slow": 20} should equal {"slow": 20, "fast": 10}
        
        So we Sort keys before hashing ( DSA finally useful ) !!

        Args:
            strategy_config: Dictionary representing the strategy configuration
            
        Returns:
            str: SHA-256 hash of the strategy configuration
        """
        # Sort keys recursively
        normalized = BacktestHashGenerator._normalize_dict(strategy_config)
        
        config_string = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
        
        return hashlib.sha256(config_string.encode('utf-8')).hexdigest()
    
    @staticmethod
    def hash_parameters(params: Dict[str, Any]) -> str:
        """
        Hash backtest parameters (commission, initial capital, etc.)
        
        Args:
            params: Dictionary of backtest parameters
            
        Returns:
            str: SHA-256 hash of parameters
        """
        # same as hash_strategy_config fn
        normalized = BacktestHashGenerator._normalize_dict(params)
        params_string = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(params_string.encode('utf-8')).hexdigest()

    @staticmethod
    def create_backtest_hash(
        data_hash: str, 
        strategy_hash: str, 
        params_hash: str
    ) -> str:
        """
        Now we use this fn to create the MASTER hash - the unique ID for this entire backtesting that user did.
        
        Args:
            data_hash: Hash of the CSV data
            strategy_hash: Hash of the strategy config
            params_hash: Hash of the parameters
            
        Returns:
            str: Master backtest hash 
        """
        combined = f"{data_hash}:{strategy_hash}:{params_hash}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    # private method
    
    @staticmethod
    def _normalize_dict(data : Dict[str,Any]) -> Dict[str,Any]:
        """
        Recursively normalize a dictionary for consistent hashing.
        
        This ensures that equivalent dictionaries always produce the same hash,
        regardless of key order or minor variations.
        """
        if isinstance(data,dict):
            return {key: BacktestHashGenerator._normalize_dict(value) for key, value in sorted(data.items())}
        elif isinstance(data,list):
            # Handle lists - try to sort if possible
            try:
                return sorted([BacktestHashGenerator._normalize_dict(item) for item in data])
            except TypeError:
                raise TypeError("Unsortable list items found")
        else:
            return data
            
