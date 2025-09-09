"""
Abstract storage interface for backtest caching.

This defines the contract that any storage implementation must follow.
Using ABC (Abstract Base Class) allows us to:
1. Define the interface clearly
2. Ensure all implementations have the same methods
3. Make it easy to switch between in-memory, SQLite, PostgreSQL, etc,  like for now we only have InMemoryStorage ... but later we can add more.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from models.backtest_models import BacktestRecord, CacheStats


class BacktestStorageInterface(ABC):
    """
    Abstract base class defining the storage interface.
    
    Any storage implementation (in-memory, SQLite, PostgreSQL, Redis, etc.)
    must inherit from this and implement all abstract methods.
    """
    
    @abstractmethod
    async def store_record(self, record: BacktestRecord) -> bool:
        """
        Store a backtest record.

        Args:
            record: Complete backtest record to store
            
        Returns:
            bool: True if stored successfully
        """
        pass
    @abstractmethod
    async def get_record(self, master_hash: str) -> Optional[BacktestRecord]:
        """
        Retrieve a backtest record by master hash.
        
        Args:
            master_hash: The unique master hash of the backtest
            
        Returns:
            BacktestRecord if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def record_exists(self, master_hash: str) -> bool:
        """
        Check if a record exists without loading it.
        
        Args:
            master_hash: The unique master hash to check
            
        Returns:
            bool: True if record exists
        """
        pass
    
    @abstractmethod
    async def get_records_by_data_hash(self, data_hash: str) -> List[BacktestRecord]:
        """
        Get all records that use the same data.
        
        Args:
            data_hash: Hash of the CSV data
            
        Returns:
            List of BacktestRecord objects
        """
        pass
    
    @abstractmethod
    async def get_records_by_strategy_hash(self, strategy_hash: str) -> List[BacktestRecord]:
        """
        Get all records that use the same strategy.
        
        Args:
            strategy_hash: Hash of the strategy configuration
            
        Returns:
            List of BacktestRecord objects
        """
        pass
    
    @abstractmethod
    async def delete_record(self, master_hash: str) -> bool:
        """
        Delete a record.
        
        Args:
            master_hash: Hash of record to delete
            
        Returns:
            bool: True if deleted successfully
        """
        pass
    
    @abstractmethod
    async def cleanup_old_records(self, days_old: int) -> int:
        """
        Clean up old records.
        
        Args:
            days_old: Delete records older than this many days
            
        Returns:
            int: Number of records deleted
        """
        pass
    
    @abstractmethod
    async def get_cache_stats(self) -> CacheStats:
        """
        Get cache statistics.
        
        Returns:
            CacheStats object with current statistics
        """
        pass
    
    @abstractmethod
    async def clear_all(self) -> bool:
        """
        Clear all stored records (useful for testing).
        
        Returns:
            bool: True if cleared successfully
        """
        pass
    
    # Context manager support for cleanup
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Subclasses can override for cleanup
        pass


class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass


class RecordNotFoundError(StorageError):
    """Exception raised when a record is not found."""
    pass


class StorageFullError(StorageError):
    """Exception raised when storage is full."""
    pass