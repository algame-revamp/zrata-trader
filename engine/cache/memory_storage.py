"""
In-memory storage implementation for backtest caching.

This implementation stores everything in memory using Python dictionaries
and provides all the features of the storage interface. It's perfect for:
- Development and testing
- Small-scale deployments
- Fast prototyping

Features:
- Thread-safe operations using asyncio locks
- LRU-style cleanup when memory limits are reached
- Comprehensive statistics tracking
- Fast lookups with multiple indexes
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from models.backtest_models import BacktestRecord, CacheStats

from .storage_interface import BacktestStorageInterface

logger = logging.getLogger(__name__)


class MemoryBacktestStorage(BacktestStorageInterface):
    """
    High-performance in-memory storage for backtest records.
    
    This implementation uses multiple indexes for fast lookups:
    - master_hash -> record (primary index)
    - data_hash -> set of master_hashes (secondary index)
    - strategy_hash -> set of master_hashes (secondary index)
    """
    def __init__(
        self,
        max_records: int = 10000,
        memory_limit_mb:Optional[int] =None
    ):
        """
        Initialize the in-memory storage.
        
        Args:
            max_records: Maximum number of records to store
            memory_limit_mb: Optional memory limit in MB
        """
        self.max_records = max_records
        self.memory_limit_mb = memory_limit_mb
        
        # Primary storage
        self._records: Dict[str,BacktestRecord] = {}
        
        # Secondary indexes for fast lockups
        self._data_index: Dict[str,Set[str]] = defaultdict(set) # basically if we add a new key that is not there this handles the creation by creating a empty set automatically
        self._strategy_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Cache stats tracking
        self._stats = CacheStats()
        
        # Thread safety
        self._lock = asyncio.Lock()
        
        # Startup logging
        logger.info(f"🧠 MemoryBacktestStorage initialized (max_records={max_records})")
        
    async def store_record(self, record:BacktestRecord) -> bool:
        """Store a backtest record with thread safety and memory management."""
        async with self._lock:
            try:
                master_hash = record.master_hash
                
                # Check if we need to make room
                await self._ensure_capacity()
                
                # Store the record
                self._records[master_hash] = record
                
                # Update secondary indexes
                self._data_index[record.identity.data_hash].add(master_hash)
                self._strategy_index[record.identity.strategy_hash].add(master_hash)
                
                # Update statistics
                self._stats.total_records = len(self._records)
                self._stats.total_data_hashes = len(self._data_index)
                self._stats.total_strategy_hashes = len(self._strategy_index)
                
                logger.debug(f"Stored record: {master_hash[:12]}...")
                return True
            except Exception as e:
                logger.error(f"Failed to store record: {e}")
                return False
            
    async def get_record(self, master_hash: str) -> Optional[BacktestRecord]:
        """Retrieve a record and update access statistics."""
        async with self._lock:
            record = self._records.get(master_hash)
            
            if record:
                # Update access statistics
                record.mark_accessed()
                self._stats.record_hit()
                logger.debug(f"Cache HIT: {master_hash[:12]}...")
            else:
                self._stats.record_miss()
                logger.debug(f"Cache MISS: {master_hash[:12]}...")
            
            return record
    
    async def record_exists(self, master_hash: str) -> bool:
        """Check if record exists without loading it."""
        async with self._lock:
            exists = master_hash in self._records
            
            if exists:
                self._stats.record_hit()
            else:
                self._stats.record_miss()
            
            return exists
        
    async def get_records_by_data_hash(self, data_hash:str) -> List[BacktestRecord]:
        """Get all records using the same data."""
        async with self._lock: 
            master_hashes = self._data_index(data_hash,set())
            records = [self._records[h] for h in master_hashes if h in self._records]       
            # Update access stats for all retrieved records
            for record in records:
                record.mark_accessed()
                self._stats.record_hit()
            
            logger.debug(f"Found {len(records)} records for data hash {data_hash[:12]}...")
            return records
        
    async def get_records_by_strategy_hash(self, strategy_hash: str) -> List[BacktestRecord]:
        """Get all records using the same strategy."""
        async with self._lock:
            master_hashes = self._strategy_index.get(strategy_hash, set())
            records = [self._records[h] for h in master_hashes if h in self._records]
            
            # Update access stats
            for record in records:
                record.mark_accessed()
                self._stats.record_hit()
            
            logger.debug(f"Found {len(records)} records for strategy hash {strategy_hash[:12]}...")
            return records
    
    async def delete_record(self, master_hash: str) -> bool:
        """Delete a record and clean up indexes."""
        async with self._lock:
            try:
                record = self._records.get(master_hash)
                if not record:
                    return False
                
                # Remove from primary storage
                del self._records[master_hash]
                
                # Clean up secondary indexes
                self._data_index[record.identity.data_hash].discard(master_hash)
                if not self._data_index[record.identity.data_hash]:
                    del self._data_index[record.identity.data_hash]
                
                self._strategy_index[record.identity.strategy_hash].discard(master_hash)
                if not self._strategy_index[record.identity.strategy_hash]:
                    del self._strategy_index[record.identity.strategy_hash]
                
                # Update stats
                self._stats.total_records = len(self._records)
                self._stats.total_data_hashes = len(self._data_index)
                self._stats.total_strategy_hashes = len(self._strategy_index)
                
                logger.debug(f"Deleted record: {master_hash[:12]}...")
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete record: {e}")
                return False
    
    async def cleanup_old_records(self, days_old: int) -> int:
        """Clean up old records based on last access time."""
        async with self._lock:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            to_delete = []
            
            # Find old records
            for master_hash, record in self._records.items():
                if record.metadata.last_accessed < cutoff_date:
                    to_delete.append(master_hash)
            
            # Delete them
            deleted_count = 0
            for master_hash in to_delete:
                if await self._delete_record_internal(master_hash):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old records (older than {days_old} days)")
            return deleted_count
    
    async def get_cache_stats(self) -> CacheStats:
        """Get current cache statistics."""
        async with self._lock:
            # Update current counts
            self._stats.total_records = len(self._records)
            self._stats.total_data_hashes = len(self._data_index)
            self._stats.total_strategy_hashes = len(self._strategy_index)
            
            return self._stats
    
    async def clear_all(self) -> bool:
        """Clear all records (useful for testing)."""
        async with self._lock:
            try:
                self._records.clear()
                self._data_index.clear()
                self._strategy_index.clear()
                self._stats = CacheStats()
                
                logger.info("Cleared all records from memory storage")
                return True
                
            except Exception as e:
                logger.error(f"Failed to clear storage: {e}")
                return False
            
    async def _ensure_capacity(self) -> None:
        """Ensure we have capacity for new records."""
        if len(self._records) >= self.max_records:
            await self._evict_lru_records(count=max(1, self.max_records // 10))  # Evict 10%
    
    async def _evict_lru_records(self, count: int) -> int:
        """
        Evict least recently used records.
        
        This implements a simple LRU (Least Recently Used) eviction policy.
        """
        if not self._records:
            return 0
        
        # Sort by last accessed time (oldest first)
        records_by_access = sorted(
            self._records.items(),
            key=lambda x: x[1].metadata.last_accessed
        )
        
        evicted = 0
        for master_hash, _ in records_by_access[:count]:
            if await self._delete_record_internal(master_hash):
                evicted += 1
        
        logger.info(f"Evicted {evicted} LRU records to make room")
        return evicted
    
    async def _delete_record_internal(self, master_hash: str) -> bool:
        """Internal delete method without locking (assumes caller has lock)."""
        try:
            record = self._records.get(master_hash)
            if not record:
                return False
            
            # Remove from primary storage
            del self._records[master_hash]
            
            # Clean up indexes
            self._data_index[record.identity.data_hash].discard(master_hash)
            if not self._data_index[record.identity.data_hash]:
                del self._data_index[record.identity.data_hash]
            
            self._strategy_index[record.identity.strategy_hash].discard(master_hash)
            if not self._strategy_index[record.identity.strategy_hash]:
                del self._strategy_index[record.identity.strategy_hash]
            
            return True
            
        except Exception:
            return False
    
    # Additional utility methods
    async def get_memory_usage_estimate(self) -> Dict[str, Any]:
        """Get estimated memory usage (rough approximation)."""
        async with self._lock:
            import sys
            
            records_size = sum(sys.getsizeof(record) for record in self._records.values())
            index_size = sys.getsizeof(self._data_index) + sys.getsizeof(self._strategy_index)
            
            return {
                "total_records": len(self._records),
                "estimated_size_bytes": records_size + index_size,
                "estimated_size_mb": round((records_size + index_size) / (1024 * 1024), 2),
                "average_record_size_bytes": records_size // max(len(self._records), 1)
            }
    
    async def get_most_accessed_records(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most frequently accessed records."""
        async with self._lock:
            sorted_records = sorted(
                self._records.values(),
                key=lambda r: r.metadata.access_count,
                reverse=True
            )
            
            return [
                {
                    "master_hash": record.master_hash[:16] + "...",
                    "access_count": record.metadata.access_count,
                    "created_at": record.metadata.created_at.isoformat(),
                    "last_accessed": record.metadata.last_accessed.isoformat(),
                    "execution_time": record.metadata.execution_time_seconds
                }
                for record in sorted_records[:limit]
            ]
    
    # Context manager implementation
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean shutdown of memory storage."""
        logger.info("Shutting down memory storage")
        # In-memory storage doesn't need special cleanup, but we could log stats
        stats = await self.get_cache_stats()
        logger.info(f"Final stats: {stats.to_dict()}")
        
# Factory function for easy creation
def create_memory_storage(max_records: int = 10000) -> MemoryBacktestStorage:
    """
    Factory function to create configured memory storage.
    
    Args:
        max_records: Maximum number of records to store in memory
        
    Returns:
        Configured MemoryBacktestStorage instance
    """
    return MemoryBacktestStorage(max_records=max_records)