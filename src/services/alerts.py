"""
Alert service for background monitoring and notifications.
"""
import asyncio
import logging
from typing import Optional, Set
from datetime import datetime, timedelta

from aiogram import Bot

from src.config import config
from src.services.proxmox import ProxmoxClient

logger = logging.getLogger(__name__)


class AlertService:
    """Background alert service for monitoring and notifications."""
    
    def __init__(self, bot: Bot, pve_client: ProxmoxClient):
        """
        Initialize alert service.
        
        Args:
            bot: Telegram bot instance
            pve_client: Proxmox client instance
        """
        self.bot = bot
        self.pve_client = pve_client
        self.running = False
        self.tasks: Set[asyncio.Task] = set()
        
        # State tracking
        self.high_load_start: Optional[datetime] = None
        self.previous_vm_states = {}
        self.alert_sent_for_load = False
    
    async def start(self) -> None:
        """Start alert service background tasks."""
        if self.running:
            logger.warning("Alert service already running")
            return
        
        self.running = True
        logger.info("Starting alert service...")
        
        # Start monitoring tasks
        task1 = asyncio.create_task(self._monitor_high_load())
        task2 = asyncio.create_task(self._monitor_vm_status())
        
        self.tasks.add(task1)
        self.tasks.add(task2)
        
        # Add done callbacks to remove completed tasks
        task1.add_done_callback(self.tasks.discard)
        task2.add_done_callback(self.tasks.discard)
        
        logger.info("Alert service started with 2 monitoring tasks")
    
    async def stop(self) -> None:
        """Stop alert service and cancel all tasks."""
        if not self.running:
            return
        
        logger.info("Stopping alert service...")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        logger.info("Alert service stopped")
    
    async def _monitor_high_load(self) -> None:
        """Monitor for sustained high CPU load."""
        while self.running:
            try:
                # Get node status
                status = await self.pve_client.get_node_status()
                
                if status:
                    cpu_usage = status.get('cpu', 0) * 100
                    
                    # Check if CPU is above threshold
                    if cpu_usage >= config.ALERT_HIGH_LOAD_THRESHOLD:
                        if self.high_load_start is None:
                            self.high_load_start = datetime.now()
                            logger.info(f"High CPU load detected: {cpu_usage:.1f}%")
                        
                        # Check if sustained for configured duration
                        load_duration = (datetime.now() - self.high_load_start).total_seconds()
                        
                        if load_duration >= config.ALERT_HIGH_LOAD_DURATION and not self.alert_sent_for_load:
                            await self._send_alert(
                                f"⚠️ *High CPU Load Alert*\n\n"
                                f"CPU usage has been above {config.ALERT_HIGH_LOAD_THRESHOLD}% "
                                f"for {int(load_duration / 60)} minutes\\.\n\n"
                                f"Current usage: {cpu_usage:.1f}%"
                            )
                            self.alert_sent_for_load = True
                    else:
                        # Reset if load drops
                        if self.high_load_start is not None:
                            logger.info(f"CPU load returned to normal: {cpu_usage:.1f}%")
                        self.high_load_start = None
                        self.alert_sent_for_load = False
                
            except Exception as e:
                logger.error(f"Error in high load monitoring: {e}")
            
            # Wait for next check
            await asyncio.sleep(config.ALERT_CHECK_INTERVAL)
    
    async def _monitor_vm_status(self) -> None:
        """Monitor for VM status changes."""
        while self.running:
            try:
                # Get all VMs
                vms = await self.pve_client.get_vms()
                
                current_states = {}
                for vm in vms:
                    vmid = vm.get('vmid')
                    status = vm.get('status')
                    name = vm.get('name', f'VM {vmid}')
                    
                    current_states[vmid] = {
                        'status': status,
                        'name': name
                    }
                
                # Check for status changes
                if self.previous_vm_states:
                    for vmid, current in current_states.items():
                        if vmid in self.previous_vm_states:
                            previous = self.previous_vm_states[vmid]
                            
                            # Status changed
                            if current['status'] != previous['status']:
                                status_emoji = '🟢' if current['status'] == 'running' else '🔴'
                                
                                await self._send_alert(
                                    f"{status_emoji} *VM Status Changed*\n\n"
                                    f"*VM:* {self._escape_markdown(current['name'])} \\(ID: {vmid}\\)\n"
                                    f"*Status:* {previous['status']} → {current['status']}"
                                )
                                
                                logger.info(
                                    f"VM {vmid} ({current['name']}) status changed: "
                                    f"{previous['status']} -> {current['status']}"
                                )
                
                # Update previous states
                self.previous_vm_states = current_states
                
            except Exception as e:
                logger.error(f"Error in VM status monitoring: {e}")
            
            # Wait for next check
            await asyncio.sleep(config.ALERT_CHECK_INTERVAL)
    
    async def _send_alert(self, message: str) -> None:
        """
        Send alert message to all admins.
        
        Args:
            message: Alert message in MarkdownV2 format
        """
        for admin_id in config.ADMIN_IDS:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode="MarkdownV2"
                )
                logger.info(f"Alert sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to send alert to admin {admin_id}: {e}")
    
    @staticmethod
    def _escape_markdown(text: str) -> str:
        """
        Escape special characters for MarkdownV2.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
