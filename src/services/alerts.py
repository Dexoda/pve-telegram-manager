"""Alert service for monitoring and notifications."""
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from aiogram import Bot

logger = logging.getLogger(__name__)


class AlertService:
    """Service for monitoring and sending alerts."""
    
    def __init__(self, bot: Bot, proxmox_client, database):
        """
        Initialize alert service.
        
        Args:
            bot: Telegram bot instance
            proxmox_client: Proxmox client instance
            database: Database instance
        """
        self.bot = bot
        self.proxmox = proxmox_client
        self.db = database
        self.running = False
        self.check_interval = 300  # 5 minutes
        self.last_vm_states: Dict[str, str] = {}
    
    async def start(self) -> None:
        """Start the alert service."""
        self.running = True
        logger.info("Alert service started")
        
        while self.running:
            try:
                await self.check_vm_status()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                logger.info("Alert service cancelled")
                break
            except Exception as e:
                logger.error(f"Error in alert service: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    def stop(self) -> None:
        """Stop the alert service."""
        self.running = False
        logger.info("Alert service stopped")
    
    async def check_vm_status(self) -> None:
        """Check VM status and send alerts if needed."""
        try:
            vms = await self.proxmox.get_all_vms()
            
            for vm in vms:
                vmid = vm.get('vmid')
                node = vm.get('node')
                status = vm.get('status')
                name = vm.get('name', f'VM {vmid}')
                vm_key = f"{node}:{vmid}"
                
                # Check if status changed
                previous_status = self.last_vm_states.get(vm_key)
                
                if previous_status and previous_status != status:
                    # VM status changed
                    await self.send_vm_status_alert(node, vmid, name, previous_status, status)
                
                # Update state
                self.last_vm_states[vm_key] = status
        except Exception as e:
            logger.error(f"Error checking VM status: {e}")
    
    async def send_vm_status_alert(
        self,
        node: str,
        vmid: int,
        name: str,
        old_status: str,
        new_status: str
    ) -> None:
        """
        Send alert about VM status change.
        
        Args:
            node: Node name
            vmid: VM ID
            name: VM name
            old_status: Previous status
            new_status: New status
        """
        try:
            # Get admin users from config
            from src.config import config
            admin_ids = config.ADMIN_IDS
            
            # Format message
            emoji = "🔴" if new_status == "stopped" else "🟢"
            message = (
                f"{emoji} *VM Status Changed*\n\n"
                f"*VM:* {name} \\({vmid}\\)\n"
                f"*Node:* {node}\n"
                f"*Status:* {old_status} → {new_status}\n"
                f"*Time:* {datetime.now().strftime('%Y\\-%m\\-%d %H:%M:%S')}"
            )
            
            # Send to all admins
            for admin_id in admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode="MarkdownV2"
                    )
                except Exception as e:
                    logger.error(f"Error sending alert to {admin_id}: {e}")
            
            # Log alert
            await self.db.add_alert(
                alert_type="vm_status_change",
                message=f"VM {name} ({vmid}) on {node}: {old_status} -> {new_status}"
            )
            
            logger.info(f"Sent VM status alert: {name} ({vmid}) {old_status} -> {new_status}")
        except Exception as e:
            logger.error(f"Error sending VM status alert: {e}")
    
    async def send_high_load_alert(self, node: str, load_avg: List[float]) -> None:
        """
        Send alert about high system load.
        
        Args:
            node: Node name
            load_avg: Load average [1min, 5min, 15min]
        """
        try:
            from src.config import config
            admin_ids = config.ADMIN_IDS
            
            message = (
                f"⚠️ *High Load Alert*\n\n"
                f"*Node:* {node}\n"
                f"*Load Average:*\n"
                f"  1min: {load_avg[0]:.2f}\n"
                f"  5min: {load_avg[1]:.2f}\n"
                f"  15min: {load_avg[2]:.2f}\n"
                f"*Time:* {datetime.now().strftime('%Y\\-%m\\-%d %H:%M:%S')}"
            )
            
            for admin_id in admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode="MarkdownV2"
                    )
                except Exception as e:
                    logger.error(f"Error sending alert to {admin_id}: {e}")
            
            await self.db.add_alert(
                alert_type="high_load",
                message=f"High load on {node}: {load_avg}"
            )
        except Exception as e:
            logger.error(f"Error sending high load alert: {e}")
    
    async def send_login_alert(self, user_id: int, username: str) -> None:
        """
        Send alert about new user login.
        
        Args:
            user_id: User ID
            username: Username
        """
        try:
            from src.config import config
            admin_ids = config.ADMIN_IDS
            
            # Don't send alert for known admins
            if user_id in admin_ids:
                return
            
            message = (
                f"🔐 *New Login Attempt*\n\n"
                f"*User ID:* {user_id}\n"
                f"*Username:* @{username if username else 'N/A'}\n"
                f"*Time:* {datetime.now().strftime('%Y\\-%m\\-%d %H:%M:%S')}\n\n"
                f"*Status:* {'✅ Authorized' if user_id in admin_ids else '❌ Unauthorized'}"
            )
            
            for admin_id in admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode="MarkdownV2"
                    )
                except Exception as e:
                    logger.error(f"Error sending alert to {admin_id}: {e}")
            
            await self.db.add_alert(
                alert_type="login",
                message=f"Login: {username} ({user_id})"
            )
        except Exception as e:
            logger.error(f"Error sending login alert: {e}")
