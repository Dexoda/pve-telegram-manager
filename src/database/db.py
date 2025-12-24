"""Database module for managing SQLite database."""
import aiosqlite
from datetime import datetime
from typing import List, Optional, Dict, Any
import os


class Database:
    """Database class for managing bot data."""
    
    def __init__(self, db_path: str):
        """
        Initialize database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None
    
    async def init(self) -> None:
        """Initialize database connection and create tables."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row
        
        # Create tables
        await self._create_tables()
    
    async def _create_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        async with self.connection.cursor() as cursor:
            # Users table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Favorites table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    vmid INTEGER NOT NULL,
                    node TEXT NOT NULL,
                    vm_type TEXT NOT NULL,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, vmid, node)
                )
            """)
            
            # Command logs table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    command TEXT NOT NULL,
                    parameters TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Alert history table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await self.connection.commit()
    
    async def close(self) -> None:
        """Close database connection."""
        if self.connection:
            await self.connection.close()
    
    # User methods
    async def add_user(
        self, 
        user_id: int, 
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> None:
        """
        Add or update user in database.
        
        Args:
            user_id: Telegram user ID
            username: Username
            first_name: First name
            last_name: Last name
        """
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, last_seen)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    last_seen = CURRENT_TIMESTAMP
            """, (user_id, username, first_name, last_name))
            await self.connection.commit()
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            User data or None
        """
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    # Favorites methods
    async def add_favorite(
        self, 
        user_id: int, 
        vmid: int, 
        node: str, 
        vm_type: str,
        name: Optional[str] = None
    ) -> bool:
        """
        Add VM to favorites.
        
        Args:
            user_id: Telegram user ID
            vmid: VM ID
            node: Node name
            vm_type: VM type (qemu or lxc)
            name: VM name
            
        Returns:
            True if added, False if already exists
        """
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO favorites (user_id, vmid, node, vm_type, name)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, vmid, node, vm_type, name))
                await self.connection.commit()
                return True
        except aiosqlite.IntegrityError:
            return False
    
    async def remove_favorite(self, user_id: int, vmid: int, node: str) -> bool:
        """
        Remove VM from favorites.
        
        Args:
            user_id: Telegram user ID
            vmid: VM ID
            node: Node name
            
        Returns:
            True if removed, False if not found
        """
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                DELETE FROM favorites 
                WHERE user_id = ? AND vmid = ? AND node = ?
            """, (user_id, vmid, node))
            await self.connection.commit()
            return cursor.rowcount > 0
    
    async def get_favorites(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get user's favorite VMs.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of favorite VMs
        """
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM favorites 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            """, (user_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def is_favorite(self, user_id: int, vmid: int, node: str) -> bool:
        """
        Check if VM is in favorites.
        
        Args:
            user_id: Telegram user ID
            vmid: VM ID
            node: Node name
            
        Returns:
            True if favorite, False otherwise
        """
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                SELECT 1 FROM favorites 
                WHERE user_id = ? AND vmid = ? AND node = ?
            """, (user_id, vmid, node))
            return await cursor.fetchone() is not None
    
    # Command logs methods
    async def log_command(
        self, 
        user_id: int, 
        username: Optional[str],
        command: str, 
        parameters: Optional[str] = None
    ) -> None:
        """
        Log command execution.
        
        Args:
            user_id: Telegram user ID
            username: Username
            command: Command name
            parameters: Command parameters
        """
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO command_logs (user_id, username, command, parameters)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, command, parameters))
            await self.connection.commit()
    
    async def get_command_logs(
        self, 
        limit: int = 100,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get command logs.
        
        Args:
            limit: Maximum number of logs to return
            user_id: Filter by user ID (optional)
            
        Returns:
            List of command logs
        """
        async with self.connection.cursor() as cursor:
            if user_id:
                await cursor.execute("""
                    SELECT * FROM command_logs 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (user_id, limit))
            else:
                await cursor.execute("""
                    SELECT * FROM command_logs 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Alert history methods
    async def add_alert(self, alert_type: str, message: str) -> None:
        """
        Add alert to history.
        
        Args:
            alert_type: Type of alert
            message: Alert message
        """
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO alert_history (alert_type, message)
                VALUES (?, ?)
            """, (alert_type, message))
            await self.connection.commit()
    
    async def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of alerts
        """
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM alert_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
