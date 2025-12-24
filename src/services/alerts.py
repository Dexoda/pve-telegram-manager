"""Background alert service for monitoring and notifications."""

import asyncio
import logging
from typing import Dict, Set
from datetime import datetime

from aiogram import Bot

from src.config import Config
from src.services.proxmox import ProxmoxClient

logger = logging.getLogger(__name__)


class AlertService:
    """Background alert service for monitoring Proxmox resources."""
    
    def __init__(self, config: Config, proxmox: ProxmoxClient, bot: Bot):
        """Initialize alert service.
        
        Args:
            config: Application configuration.
            proxmox: Proxmox client instance.
            bot: Telegram bot instance.
        """
        self.config = config
        self.proxmox = proxmox
        self.bot = bot
        self.running = False
        self.task = None
        
        # State tracking
        self.high_load_start_time: Dict[str, datetime] = {}
        self.vm_states: Dict[int, str] = {}
        self.alerted_nodes: Set[str] = set()
    
    async def start(self):
        """Start the alert service."""
        if self.running:
            logger.warning("Alert service is already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._monitor_loop())
        logger.info("Alert service started")
    
    async def stop(self):
        """Stop the alert service."""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Alert service stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                await self._check_alerts()
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
            
            # Wait for next check interval
            await asyncio.sleep(self.config.alerts.check_interval)
    
    async def _check_alerts(self):
        """Check all alert conditions."""
        try:
            # Check high CPU load
            await self._check_high_load()
            
            # Check VM status changes
            await self._check_vm_status_changes()
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    async def _check_high_load(self):
        """Check for high CPU load conditions."""
        try:
            nodes = await self.proxmox.get_nodes()
            current_time = datetime.now()
            
            for node in nodes:
                node_name = node.get('node', 'unknown')
                
                try:
                    status = await self.proxmox.get_node_status(node_name)
                    cpu_usage = status.get('cpu', 0) * 100
                    
                    # Check if CPU usage is above threshold
                    if cpu_usage > self.config.alerts.high_load_threshold:
                        # Track when high load started
                        if node_name not in self.high_load_start_time:
                            self.high_load_start_time[node_name] = current_time
                            logger.info(f"High CPU load detected on {node_name}: {cpu_usage:.1f}%")
                        else:
                            # Check if high load has persisted for duration threshold
                            duration = (current_time - self.high_load_start_time[node_name]).total_seconds()
                            
                            if duration >= self.config.alerts.high_load_duration:
                                # Send alert if not already alerted for this occurrence
                                if node_name not in self.alerted_nodes:
                                    await self._send_high_load_alert(node_name, cpu_usage, duration)
                                    self.alerted_nodes.add(node_name)
                    else:
                        # CPU load is normal, reset tracking
                        if node_name in self.high_load_start_time:
                            del self.high_load_start_time[node_name]
                        if node_name in self.alerted_nodes:
                            self.alerted_nodes.remove(node_name)
                            logger.info(f"CPU load normalized on {node_name}")
                
                except Exception as e:
                    logger.error(f"Failed to check load for {node_name}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to check high load: {e}")
    
    async def _check_vm_status_changes(self):
        """Check for VM status changes."""
        try:
            vms = await self.proxmox.get_vms()
            
            for vm in vms:
                vmid = vm.get('vmid')
                current_status = vm.get('status', 'unknown')
                
                # Check if we have a previous status recorded
                if vmid in self.vm_states:
                    previous_status = self.vm_states[vmid]
                    
                    # Check if status changed
                    if current_status != previous_status:
                        await self._send_vm_status_change_alert(vm, previous_status, current_status)
                
                # Update stored status
                self.vm_states[vmid] = current_status
        
        except Exception as e:
            logger.error(f"Failed to check VM status changes: {e}")
    
    async def _send_high_load_alert(self, node_name: str, cpu_usage: float, duration: float):
        """Send high CPU load alert to admins.
        
        Args:
            node_name: Node name.
            cpu_usage: Current CPU usage percentage.
            duration: Duration of high load in seconds.
        """
        duration_min = int(duration / 60)
        
        message = (
            f"🔴 *High CPU Load Alert*\n\n"
            f"*Node:* {self._escape_markdown(node_name)}\n"
            f"*CPU Usage:* {cpu_usage:.1f}%\n"
            f"*Duration:* {duration_min} minutes\n"
            f"*Threshold:* {self.config.alerts.high_load_threshold}%\n\n"
            f"_CPU load has been above threshold for {duration_min} minutes\\._"
        )
        
        await self._send_to_admins(message)
        logger.info(f"Sent high load alert for {node_name}")
    
    async def _send_vm_status_change_alert(self, vm: Dict, old_status: str, new_status: str):
        """Send VM status change alert to admins.
        
        Args:
            vm: VM information dictionary.
            old_status: Previous VM status.
            new_status: Current VM status.
        """
        vmid = vm.get('vmid')
        vm_name = vm.get('name', f'VM {vmid}')
        vm_type = vm.get('type', 'qemu').upper()
        node = vm.get('node', 'unknown')
        
        # Status emojis
        status_emoji_map = {
            'running': '🟢',
            'stopped': '🔴',
            'paused': '🟡',
        }
        
        old_emoji = status_emoji_map.get(old_status, '⚪')
        new_emoji = status_emoji_map.get(new_status, '⚪')
        
        message = (
            f"🔄 *VM Status Changed*\n\n"
            f"*Name:* {self._escape_markdown(vm_name)}\n"
            f"*ID:* {vmid}\n"
            f"*Type:* {vm_type}\n"
            f"*Node:* {self._escape_markdown(node)}\n\n"
            f"*Status Change:*\n"
            f"{old_emoji} {self._escape_markdown(old_status.title())} → "
            f"{new_emoji} {self._escape_markdown(new_status.title())}"
        )
        
        await self._send_to_admins(message)
        logger.info(f"Sent VM status change alert for {vmid}: {old_status} -> {new_status}")
    
    async def _send_to_admins(self, message: str):
        """Send message to all admins.
        
        Args:
            message: Message text in MarkdownV2 format.
        """
        for admin_id in self.config.telegram.admin_ids:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode="MarkdownV2"
                )
            except Exception as e:
                logger.error(f"Failed to send alert to admin {admin_id}: {e}")
    
    @staticmethod
    def _escape_markdown(text: str) -> str:
        """Escape text for MarkdownV2.
        
        Args:
            text: Text to escape.
            
        Returns:
            str: Escaped text.
        """
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        for char in escape_chars:
            text = str(text).replace(char, f'\\{char}')
        return text
