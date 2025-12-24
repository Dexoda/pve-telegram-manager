"""
Database manager using aiosqlite for async SQLite operations.
"""
import aiosqlite
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class Database:
    """Async SQLite database manager."""
    
    def __init__(self, db_path: str):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_directory()
    
    def _ensure_directory(self) -> None:
        """Ensure database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    async def initialize(self) -> None:
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Favorites table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    user_id INTEGER,
                    vmid INTEGER,
                    name TEXT,
                    node TEXT,
                    vm_type TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, vmid)
                )
            """)
            
            # Usage logs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    command TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def add_user(self, user_id: int, username: Optional[str] = None) -> None:
        """
        Add or update user in database.
        
        Args:
            user_id: Telegram user ID
            username: Telegram username
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (user_id, username, first_seen, last_seen)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    last_seen = CURRENT_TIMESTAMP
            """, (user_id, username))
            await db.commit()
    
    async def log_command(self, user_id: int, username: Optional[str], command: str) -> None:
        """
        Log command usage.
        
        Args:
            user_id: Telegram user ID
            username: Telegram username
            command: Command executed
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO usage_logs (user_id, username, command)
                VALUES (?, ?, ?)
            """, (user_id, username, command))
            await db.commit()
    
    async def add_favorite(
        self,
        user_id: int,
        vmid: int,
        name: str,
        node: str,
        vm_type: str
    ) -> bool:
        """
        Add VM to user's favorites.
        
        Args:
            user_id: Telegram user ID
            vmid: VM ID
            name: VM name
            node: Proxmox node name
            vm_type: VM type (qemu or lxc)
            
        Returns:
            True if added, False if already exists
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO favorites (user_id, vmid, name, node, vm_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, vmid, name, node, vm_type))
                await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False
    
    async def remove_favorite(self, user_id: int, vmid: int) -> bool:
        """
        Remove VM from user's favorites.
        
        Args:
            user_id: Telegram user ID
            vmid: VM ID
            
        Returns:
            True if removed, False if not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM favorites
                WHERE user_id = ? AND vmid = ?
            """, (user_id, vmid))
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_favorites(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get user's favorite VMs.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of favorite VMs
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT vmid, name, node, vm_type, added_at
                FROM favorites
                WHERE user_id = ?
                ORDER BY added_at DESC
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def is_favorite(self, user_id: int, vmid: int) -> bool:
        """
        Check if VM is in user's favorites.
        
        Args:
            user_id: Telegram user ID
            vmid: VM ID
            
        Returns:
            True if favorite, False otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT 1 FROM favorites
                WHERE user_id = ? AND vmid = ?
            """, (user_id, vmid)) as cursor:
                result = await cursor.fetchone()
                return result is not None
    
    async def get_usage_stats(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent usage statistics.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of usage log entries
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT user_id, username, command, timestamp
                FROM usage_logs
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
