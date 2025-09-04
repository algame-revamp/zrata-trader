
"""
These models represent the core data structures in our system.
"""

from __future__ import \
    annotations  # enables a feature called postponed evaluation of annotations Instead of evaluating a type hint the moment a function or class is defined, it stores the hint as a string. The actual evaluation is "postponed" until it's needed by a runtime library or a static type checker. ( Python is pretty cool )

import pickle
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True) # frozen so it is good for hashing
class BacktestIdentity:
    """
    Immutable identity of a backtest - the unique fingerprint.
    
    This is separate from results because identity never changes,
    but we might want to update access statistics.
    """
    data_hash: str
    strategy_hash: str
    params_hash: str
    master_hash: str
    
    def __post_init__(self):
        """Validae the hash formats after creation"""
        hashes = [
            self.data_hash, 
            self.strategy_hash, 
            self.params_hash, 
            self.master_hash
        ]
        for hash_val in hashes:
            if not isinstance(hash_val,str) or len(hash_val) != 64: # we will use SHA-256 (or double SHA-256) for hashing, the hash output is 32 bytes. When represented as a hex string, each byte takes 2 hex characters → 32 * 2 = 64.
                raise ValueError(f"Invalid hash format: {hash_val}")
            
@dataclass
class BacktestMetadata:
    """Metadata about a backtest, including timestamps and access stats."""
    created_at: datetime
    last_accessed: datetime
    access_count: int = 1
    execution_time_seconds: float = 0.0
    data_filename: Optional[str] = None
    data_size_bytes: Optional[int] = 0
    data_rows: int = 0
    
    def mark_accessed(self):
        """Update access statistics."""
        self.last_accessed = datetime.now()
        self.access_count += 1
        
@dataclass
class BacktestResult:
    """Actual bactest computed results"""
    raw_results: bytes  # Pickled raw results
    summary: Dict[str, Any]  # Summary statistics
    equity_curve: List[Dict[str, Any]]  # Time series data for equity curve
    trades: Optional[List[Dict[str, Any]]] = field(default_factory=list)  # List of trades

    @classmethod
    def from_simulation(cls, simulation_data: Dict[str, Any]) -> BacktestResult:
        """Create BacktestResults from simulation data."""
        return cls(
            raw_results=pickle.dumps(simulation_data),
            stats=simulation_data.get('stats', {}),
            equity_curve=simulation_data.get('equity_curve', []),
            trades=simulation_data.get('trades', [])
        )
    
    def get_raw_results(self) -> Any:
        """Unpickle and return raw results."""
        return pickle.loads(self.raw_results)
    
    
@dataclass
class BacktestRecord:
    """
    Complete backtest record combining identity, metadata, and results.
    
    This is the main data structure that gets stored and retrieved.
    """
    identity: BacktestIdentity
    metadata: BacktestMetadata
    results: BacktestResult
    
    @property
    def master_hash(self) -> str:
        """Convenience property to get master hash."""
        return self.identity.master_hash
    
    @property
    def created_at(self) -> datetime:
        """Convenience property to get creation time."""
        return self.metadata.created_at
    
    def mark_accessed(self) -> None:
        """Mark this record as accessed."""
        self.metadata.mark_accessed()
    
    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "master_hash": self.identity.master_hash,
            "data_hash": self.identity.data_hash[:16] + "...",  # Truncated for display
            "strategy_hash": self.identity.strategy_hash[:16] + "...",
            "stats": self.results.stats,
            "equity_curve": self.results.equity_curve,
            "created_at": self.metadata.created_at.isoformat(),
            "last_accessed": self.metadata.last_accessed.isoformat(),
            "access_count": self.metadata.access_count,
            "execution_time_seconds": self.metadata.execution_time_seconds,
            "data_filename": self.metadata.data_filename,
            "data_rows": self.metadata.data_rows
        }
        
@dataclass
class CacheStats:
    """Statistics about the cache performance."""
    total_records: int = 0
    total_data_hashes: int = 0
    total_strategy_hashes: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_requests: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate
    
    def record_hit(self) -> None:
        """Record a cache hit."""
        self.cache_hits += 1
        self.total_requests += 1
    
    def record_miss(self) -> None:
        """Record a cache miss."""
        self.cache_misses += 1
        self.total_requests += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "total_records": self.total_records,
            "total_data_hashes": self.total_data_hashes,
            "total_strategy_hashes": self.total_strategy_hashes,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate * 100, 2),
            "miss_rate": round(self.miss_rate * 100, 2)
        }