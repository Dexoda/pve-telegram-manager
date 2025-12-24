"""SQLite database manager with aiosqlite."""

import aiosqlite
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class Database:
    """Async SQLite database manager."""
    
    def __init__(self, db_path: str):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    async def init_db(self):
        """Initialize database schema."""
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
    
    async def update_user(self, user_id: int, username: Optional[str] = None):
        """Update or insert user information.
        
        Args:
            user_id: Telegram user ID.
            username: Telegram username.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (user_id, username, first_seen, last_seen)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = COALESCE(?, username),
                    last_seen = CURRENT_TIMESTAMP
            """, (user_id, username, username))
            await db.commit()
    
    async def log_command(self, user_id: int, username: Optional[str], command: str):
        """Log command usage.
        
        Args:
            user_id: Telegram user ID.
            username: Telegram username.
            command: Command name.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO usage_logs (user_id, username, command, timestamp)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
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
        """Add VM to favorites.
        
        Args:
            user_id: Telegram user ID.
            vmid: VM ID.
            name: VM name.
            node: Proxmox node name.
            vm_type: VM type (qemu or lxc).
            
        Returns:
            bool: True if added, False if already exists.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO favorites (user_id, vmid, name, node, vm_type, added_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, vmid, name, node, vm_type))
                await db.commit()
                return True
        except aiosqlite.IntegrityError:
            return False
    
    async def remove_favorite(self, user_id: int, vmid: int) -> bool:
        """Remove VM from favorites.
        
        Args:
            user_id: Telegram user ID.
            vmid: VM ID.
            
        Returns:
            bool: True if removed, False if not found.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM favorites
                WHERE user_id = ? AND vmid = ?
            """, (user_id, vmid))
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_favorites(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's favorite VMs.
        
        Args:
            user_id: Telegram user ID.
            
        Returns:
            List[Dict]: List of favorite VMs.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT vmid, name, node, vm_type, added_at
                FROM favorites
                WHERE user_id = ?
                ORDER BY added_at DESC
            """, (user_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def is_favorite(self, user_id: int, vmid: int) -> bool:
        """Check if VM is in favorites.
        
        Args:
            user_id: Telegram user ID.
            vmid: VM ID.
            
        Returns:
            bool: True if VM is in favorites.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT 1 FROM favorites
                WHERE user_id = ? AND vmid = ?
            """, (user_id, vmid))
            result = await cursor.fetchone()
            return result is not None
    
    async def get_usage_stats(self, user_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get usage statistics.
        
        Args:
            user_id: Optional user ID filter.
            limit: Maximum number of records.
            
        Returns:
            List[Dict]: Usage log records.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if user_id:
                cursor = await db.execute("""
                    SELECT * FROM usage_logs
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor = await db.execute("""
                    SELECT * FROM usage_logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
