"""
Database persistence layer for HyperTrail bot state management.
Provides SQLite storage for active bots that survive application restarts.
Uses direct imports to avoid package-relative import issues.
"""

import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

# Direct imports
import sys
sys.path.insert(0, str(__file__).replace('/engine/persistence.py', '')[:-1])

try:
    from constants import DATABASE_NAME, LOGS_DIR
except ImportError:
    DATABASE_NAME = "hypertrail_bots.db"
    LOGS_DIR = "logs"


logger = logging.getLogger(__name__)


class DatabasePersistence:
    """SQLite database for persisting bot states across sessions."""
    
    def __init__(self, database_path: Optional[str] = None):
        self.database_path = Path(database_path) if database_path else Path(LOGS_DIR) / DATABASE_NAME
        self._establish_connection()
        
    def _establish_connection(self) -> None:
        """Create database connection and initialize tables."""
        try:
            os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
            
            conn = sqlite3.connect(str(self.database_path))
            cursor = conn.cursor()
            
            # Create bot_config table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bots (
                    bot_id TEXT PRIMARY KEY,
                    coin TEXT NOT NULL,
                    trail_type TEXT NOT NULL,
                    size_usd REAL NOT NULL,
                    offset_pct REAL NOT NULL,
                    max_chase_pct REAL NOT NULL,
                    reduce_only INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create bot_state table for runtime state tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    oid INTEGER,
                    current_limit_price REAL NOT NULL,
                    last_trail_reference REAL NOT NULL,
                    delta_pct REAL DEFAULT 0.0,
                    times_active_minutes INTEGER DEFAULT 0,
                    fills_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bot_id) REFERENCES bots(bot_id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Database initialized at {self.database_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def _get_cursor(self):
        """Context manager for safe database operations."""
        conn = None
        try:
            conn = sqlite3.connect(str(self.database_path))
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def persist_bot_config(self, config: Dict[str, Any]) -> bool:
        """Save bot configuration to database."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute("""
                    INSERT OR REPLACE INTO bots 
                    (bot_id, coin, trail_type, size_usd, offset_pct, max_chase_pct, reduce_only, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    config.get('bot_id', 'unknown'),
                    config.get('coin'),
                    config.get('trail_type', ''),
                    config.get('size_usd', 0),
                    config.get('offset_pct', 0),
                    config.get('max_chase_pct', 0),
                    1 if config.get('reduce_only') else 0,
                    1 if config.get('is_active') else 0,
                ))
            
            logger.info(f"Persisted bot config for {config.get('bot_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to persist bot config: {e}")
            return False
    
    async def get_bot_statistics(self) -> Dict[str, Any]:
        """Get summary statistics about persisted bots."""
        try:
            with self._get_cursor() as cursor:
                total = 0
                active = 0
                
                cursor.execute("SELECT COUNT(*) FROM bots")
                total = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM bots WHERE is_active = 1")
                active = cursor.fetchone()[0]
                
                return {
                    "total_bots_created": total,
                    "active_bots": active,
                    "inactive_bots": total - active
                }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    async def load_all_bots(self) -> Dict[str, Dict[str, Any]]:
        """Load all bot configurations from database."""
        try:
            result = {}
            with self._get_cursor() as cursor:
                cursor.execute("""
                    SELECT bot_id, coin, trail_type, size_usd, offset_pct, 
                           max_chase_pct, reduce_only, is_active, created_at, oid,
                           current_limit_price, last_trail_reference, delta_pct,
                           times_active_minutes, fills_count, status
                    FROM bots
                """)
                
                for row in cursor.fetchall():
                    bot_id = row[0]
                    result[bot_id] = {
                        "id": bot_id,
                        "coin": row[1],
                        "trail_type": row[2],
                        "size_usd": row[3],
                        "offset_pct": row[4],
                        "max_chase_pct": row[5],
                        "order_side": "buy" if row[6] else "sell",  # reduce_only=1 means buy
                        "status": "ACTIVE" if row[7] else "INACTIVE",
                        "created_at": row[8],
                        "oid": row[9] if row[9] else None,
                        "current_limit_price": row[10] if row[10] else None,
                        "last_trail_reference": row[11] if row[11] else None,
                        "delta_pct": row[12] if row[12] else None,
                        "times_active_minutes": row[13] if row[13] else 0,
                        "fills_count": row[14] if row[14] else 0,
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to load all bots: {e}")
            return {}
    
    async def delete_bot(self, bot_id: str) -> bool:
        """Delete a bot from the database."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute("DELETE FROM bots WHERE bot_id = ?", (bot_id,))
                
                if cursor.rowcount > 0:
                    logger.info(f"Deleted bot {bot_id}")
                    return True
                else:
                    logger.warning(f"Bot {bot_id} not found")
                    return False
            
        except Exception as e:
            logger.error(f"Failed to delete bot {bot_id}: {e}")
            return False
