"""
Monitoring handlers for system resources.
"""
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.services.proxmox import ProxmoxClient
from src.services.ssh_client import SSHClient
from src.database.db import Database
from src.keyboards.inline import get_monitoring_menu_keyboard, get_back_keyboard
from src.utils.formatters import escape_markdown
from src.utils.progress_bars import create_progress_bar, format_bytes, format_uptime

logger = logging.getLogger(__name__)

router = Router()

# Global instances (will be set in main.py)
pve_client: Optional[ProxmoxClient] = None
ssh_client: Optional[SSHClient] = None
db: Optional[Database] = None


def set_services(proxmox: ProxmoxClient, ssh: SSHClient, database: Database) -> None:
    """Set global service instances."""
    global pve_client, ssh_client, db
    pve_client = proxmox
    ssh_client = ssh
    db = database


@router.callback_query(F.data == "menu_monitoring")
async def menu_monitoring(callback: CallbackQuery) -> None:
    """
    Handle monitoring menu callback.
    
    Args:
        callback: Callback query object
    """
    text = (
        "📊 *Monitoring*\n\n"
        "Select what you want to monitor:"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=get_monitoring_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "mon_node_status")
async def mon_node_status(callback: CallbackQuery) -> None:
    """
    Handle node status callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Loading node status...")
    
    try:
        # Get node status
        status = await pve_client.get_node_status()
        
        if not status:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "Failed to retrieve node status\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_monitoring")
            )
            return
        
        # Parse status
        cpu_usage = status.get('cpu', 0) * 100
        memory_used = status.get('memory', {}).get('used', 0)
        memory_total = status.get('memory', {}).get('total', 1)
        memory_percent = (memory_used / memory_total * 100) if memory_total > 0 else 0
        
        uptime = status.get('uptime', 0)
        loadavg = status.get('loadavg', [0, 0, 0])
        
        # Get disk info
        rootfs = status.get('rootfs', {})
        disk_used = rootfs.get('used', 0)
        disk_total = rootfs.get('total', 1)
        disk_percent = (disk_used / disk_total * 100) if disk_total > 0 else 0
        
        # Format output
        text = "🖥 *Node Status*\n\n"
        
        # CPU
        cpu_bar = create_progress_bar(cpu_usage, 100)
        text += f"*CPU Usage:* {cpu_usage:.1f}%\n"
        text += f"`{cpu_bar}` {cpu_usage:.1f}%\n\n"
        
        # Memory
        mem_bar = create_progress_bar(memory_percent, 100)
        text += f"*Memory:* {format_bytes(memory_used)} / {format_bytes(memory_total)}\n"
        text += f"`{mem_bar}` {memory_percent:.1f}%\n\n"
        
        # Disk
        disk_bar = create_progress_bar(disk_percent, 100)
        text += f"*Root Disk:* {format_bytes(disk_used)} / {format_bytes(disk_total)}\n"
        text += f"`{disk_bar}` {disk_percent:.1f}%\n\n"
        
        # Uptime
        text += f"*Uptime:* {escape_markdown(format_uptime(uptime))}\n\n"
        
        # Load average
        text += f"*Load Average:*\n"
        text += f"1 min: {loadavg[0]:.2f}\n"
        text += f"5 min: {loadavg[1]:.2f}\n"
        text += f"15 min: {loadavg[2]:.2f}\n"
        
        # Log action
        if db:
            await db.log_command(
                callback.from_user.id,
                callback.from_user.username,
                "mon_node_status"
            )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_monitoring")
        )
        
    except Exception as e:
        logger.error(f"Error getting node status: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to get node status: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_monitoring")
        )


@router.callback_query(F.data == "mon_cpu_temp")
async def mon_cpu_temp(callback: CallbackQuery) -> None:
    """
    Handle CPU temperature callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Loading CPU temperature...")
    
    try:
        if not ssh_client:
            await callback.answer("SSH client not available", show_alert=True)
            return
        
        # Get CPU temperature
        temps = await ssh_client.get_cpu_temperature()
        
        if not temps:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "Failed to retrieve CPU temperature\\.\n"
                "Make sure lm\\-sensors is installed\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_monitoring")
            )
            return
        
        # Format output
        text = "🌡 *CPU Temperature*\n\n"
        
        for chip, readings in temps.items():
            text += f"*{escape_markdown(chip)}:*\n"
            
            for sensor, value in readings.items():
                if 'input' in sensor:
                    sensor_name = sensor.replace('_input', '').replace('_', ' ').title()
                    text += f"• {escape_markdown(sensor_name)}: {value:.1f}°C\n"
            
            text += "\n"
        
        # Log action
        if db:
            await db.log_command(
                callback.from_user.id,
                callback.from_user.username,
                "mon_cpu_temp"
            )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_monitoring")
        )
        
    except Exception as e:
        logger.error(f"Error getting CPU temperature: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to get CPU temperature: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_monitoring")
        )


@router.callback_query(F.data == "mon_disk_status")
async def mon_disk_status(callback: CallbackQuery) -> None:
    """
    Handle disk status callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Loading disk status...")
    
    try:
        if not ssh_client:
            await callback.answer("SSH client not available", show_alert=True)
            return
        
        # Get disk info
        disk_info = await ssh_client.get_disk_info()
        
        if not disk_info:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "Failed to retrieve disk information\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_monitoring")
            )
            return
        
        # Parse disk info
        text = "💽 *Disk Status*\n\n"
        
        lines = disk_info.strip().split('\n')
        if len(lines) > 1:
            # Skip header line
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 6:
                    filesystem = parts[0]
                    size = parts[1]
                    used = parts[2]
                    avail = parts[3]
                    percent = parts[4]
                    mount = parts[5]
                    
                    # Skip some filesystems
                    if filesystem.startswith('/dev/') or mount in ['/', '/boot', '/home']:
                        text += f"*{escape_markdown(mount)}*\n"
                        text += f"Device: `{escape_markdown(filesystem)}`\n"
                        text += f"Size: {escape_markdown(size)} \\| Used: {escape_markdown(used)} \\| Available: {escape_markdown(avail)}\n"
                        text += f"Usage: {escape_markdown(percent)}\n\n"
        
        # Log action
        if db:
            await db.log_command(
                callback.from_user.id,
                callback.from_user.username,
                "mon_disk_status"
            )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_monitoring")
        )
        
    except Exception as e:
        logger.error(f"Error getting disk status: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to get disk status: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_monitoring")
        )


@router.callback_query(F.data == "mon_smart_status")
async def mon_smart_status(callback: CallbackQuery) -> None:
    """
    Handle SMART status callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Loading SMART status...")
    
    try:
        if not ssh_client:
            await callback.answer("SSH client not available", show_alert=True)
            return
        
        # Get SMART status for common disk devices
        devices = ["/dev/sda", "/dev/sdb", "/dev/nvme0n1"]
        
        text = "🔍 *SMART Status*\n\n"
        found_device = False
        
        for device in devices:
            smart_output = await ssh_client.get_smart_status(device)
            
            if smart_output and "PASSED" in smart_output:
                found_device = True
                text += f"*{escape_markdown(device)}:* ✅ PASSED\n"
            elif smart_output and "FAILED" in smart_output:
                found_device = True
                text += f"*{escape_markdown(device)}:* ❌ FAILED\n"
        
        if not found_device:
            text += "_No SMART\\-capable devices found or smartmontools not installed\\._\n"
        
        # Log action
        if db:
            await db.log_command(
                callback.from_user.id,
                callback.from_user.username,
                "mon_smart_status"
            )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_monitoring")
        )
        
    except Exception as e:
        logger.error(f"Error getting SMART status: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to get SMART status: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_monitoring")
        )


@router.callback_query(F.data == "mon_network")
async def mon_network(callback: CallbackQuery) -> None:
    """
    Handle network traffic callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Loading network statistics...")
    
    try:
        if not ssh_client:
            await callback.answer("SSH client not available", show_alert=True)
            return
        
        # Get network stats
        net_stats = await ssh_client.get_network_stats()
        
        if not net_stats:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "Failed to retrieve network statistics\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_monitoring")
            )
            return
        
        # Parse network stats
        text = "🌐 *Network Traffic*\n\n"
        
        lines = net_stats.strip().split('\n')
        for line in lines[2:]:  # Skip first two header lines
            parts = line.split()
            if len(parts) >= 10:
                interface = parts[0].rstrip(':')
                
                # Skip loopback
                if interface == 'lo':
                    continue
                
                rx_bytes = int(parts[1])
                tx_bytes = int(parts[9])
                
                text += f"*{escape_markdown(interface)}:*\n"
                text += f"↓ RX: {escape_markdown(format_bytes(rx_bytes))}\n"
                text += f"↑ TX: {escape_markdown(format_bytes(tx_bytes))}\n\n"
        
        # Log action
        if db:
            await db.log_command(
                callback.from_user.id,
                callback.from_user.username,
                "mon_network"
            )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_monitoring")
        )
        
    except Exception as e:
        logger.error(f"Error getting network stats: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to get network statistics: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_monitoring")
        )


@router.callback_query(F.data == "mon_load_avg")
async def mon_load_avg(callback: CallbackQuery) -> None:
    """
    Handle load average callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Loading system load...")
    
    try:
        if not ssh_client:
            await callback.answer("SSH client not available", show_alert=True)
            return
        
        # Get load average
        load_output = await ssh_client.get_load_average()
        
        if not load_output:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "Failed to retrieve load average\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_monitoring")
            )
            return
        
        # Parse load average
        parts = load_output.strip().split()
        
        if len(parts) >= 3:
            load_1 = float(parts[0])
            load_5 = float(parts[1])
            load_15 = float(parts[2])
            
            text = "⚡ *System Load Average*\n\n"
            text += f"*1 minute:* {load_1:.2f}\n"
            text += f"*5 minutes:* {load_5:.2f}\n"
            text += f"*15 minutes:* {load_15:.2f}\n\n"
            
            # Add load interpretation
            if load_1 > 4.0:
                text += "⚠️ _High load detected\\!_"
            elif load_1 > 2.0:
                text += "⚡ _Moderate load_"
            else:
                text += "✅ _Normal load_"
            
            # Log action
            if db:
                await db.log_command(
                    callback.from_user.id,
                    callback.from_user.username,
                    "mon_load_avg"
                )
            
            await callback.message.edit_text(
                text,
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_monitoring")
            )
        else:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "Failed to parse load average\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_monitoring")
            )
        
    except Exception as e:
        logger.error(f"Error getting load average: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to get load average: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_monitoring")
        )
