"""Resource monitoring handlers."""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.config import Config
from src.database import Database
from src.services.proxmox import ProxmoxClient
from src.services.ssh_client import SSHClient
from src.keyboards.inline import get_monitoring_keyboard, get_back_button
from src.utils.formatters import escape_markdown, format_bytes, format_uptime
from src.utils.progress_bars import create_percentage_bar

logger = logging.getLogger(__name__)

router = Router()

# Global state for dependency injection
_config: Config = None
_db: Database = None
_proxmox: ProxmoxClient = None
_ssh: SSHClient = None


def setup_monitoring_router(config: Config, db: Database, proxmox: ProxmoxClient, ssh: SSHClient):
    """Setup monitoring router with dependencies.
    
    Args:
        config: Application configuration.
        db: Database instance.
        proxmox: Proxmox client instance.
        ssh: SSH client instance.
    """
    global _config, _db, _proxmox, _ssh
    _config = config
    _db = db
    _proxmox = proxmox
    _ssh = ssh


@router.callback_query(F.data == "menu:monitoring")
async def callback_monitoring_menu(callback: CallbackQuery):
    """Handle monitoring menu callback.
    
    Args:
        callback: Callback query.
    """
    await _db.log_command(callback.from_user.id, callback.from_user.username, "monitoring:menu")
    
    await callback.message.edit_text(
        "📊 *Monitoring*\n\n"
        "Select monitoring option:",
        reply_markup=get_monitoring_keyboard(),
        parse_mode="MarkdownV2"
    )
    await callback.answer()


@router.callback_query(F.data == "monitor:node")
async def callback_monitor_node(callback: CallbackQuery):
    """Handle node status monitoring callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading node status...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "monitor:node")
    
    try:
        # Get all nodes
        nodes = await _proxmox.get_nodes()
        
        if not nodes:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "No nodes found\\.",
                reply_markup=get_back_button("menu:monitoring"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Build status message for each node
        messages = ["💻 *Node Status*\n"]
        
        for node in nodes:
            node_name = node.get('node', 'unknown')
            
            try:
                status = await _proxmox.get_node_status(node_name)
                
                # CPU usage
                cpu_usage = status.get('cpu', 0) * 100
                cpus = status.get('cpuinfo', {}).get('cpus', 1)
                
                # Memory usage
                mem_used = status.get('memory', {}).get('used', 0)
                mem_total = status.get('memory', {}).get('total', 1)
                mem_percent = (mem_used / mem_total * 100) if mem_total > 0 else 0
                
                # Disk usage
                disk_used = status.get('rootfs', {}).get('used', 0)
                disk_total = status.get('rootfs', {}).get('total', 1)
                disk_percent = (disk_used / disk_total * 100) if disk_total > 0 else 0
                
                # Uptime
                uptime = status.get('uptime', 0)
                
                # Load average
                loadavg = status.get('loadavg', [0, 0, 0])
                load_1 = loadavg[0] if len(loadavg) > 0 else 0
                load_5 = loadavg[1] if len(loadavg) > 1 else 0
                load_15 = loadavg[2] if len(loadavg) > 2 else 0
                
                messages.append(f"\n📍 *{escape_markdown(node_name)}*")
                messages.append(f"*Uptime:* {escape_markdown(format_uptime(uptime))}")
                messages.append("")
                
                messages.append(f"*CPU Usage:* {cpu_usage:.1f}% \\({cpus} cores\\)")
                messages.append(create_percentage_bar(cpu_usage) + f" {cpu_usage:.1f}%")
                messages.append("")
                
                messages.append(f"*Memory:* {escape_markdown(format_bytes(mem_used))} / {escape_markdown(format_bytes(mem_total))}")
                messages.append(create_percentage_bar(mem_percent) + f" {mem_percent:.1f}%")
                messages.append("")
                
                messages.append(f"*Root Disk:* {escape_markdown(format_bytes(disk_used))} / {escape_markdown(format_bytes(disk_total))}")
                messages.append(create_percentage_bar(disk_percent) + f" {disk_percent:.1f}%")
                messages.append("")
                
                messages.append(f"*Load Avg:* {load_1:.2f}, {load_5:.2f}, {load_15:.2f}")
                
            except Exception as e:
                logger.error(f"Failed to get status for node {node_name}: {e}")
                messages.append(f"\n📍 *{escape_markdown(node_name)}*")
                messages.append(f"⚠️ Failed to get status: {escape_markdown(str(e))}")
        
        text = "\n".join(messages)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("menu:monitoring"),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get node status: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve node status: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:monitoring"),
            parse_mode="MarkdownV2"
        )


@router.callback_query(F.data == "monitor:temp")
async def callback_monitor_temp(callback: CallbackQuery):
    """Handle CPU temperature monitoring callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading CPU temperature...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "monitor:temp")
    
    try:
        temp_output = await _ssh.get_cpu_temperature()
        
        if not temp_output:
            await callback.message.edit_text(
                "⚠️ *CPU Temperature*\n\n"
                "Temperature sensors not available or lm\\-sensors not installed\\.\n\n"
                "_Install with: `apt install lm-sensors && sensors-detect`_",
                reply_markup=get_back_button("menu:monitoring"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Format output
        escaped_output = escape_markdown(temp_output.strip())
        
        text = (
            "🌡️ *CPU Temperature*\n\n"
            f"```\n{escaped_output}\n```"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("menu:monitoring"),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get CPU temperature: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve CPU temperature: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:monitoring"),
            parse_mode="MarkdownV2"
        )


@router.callback_query(F.data == "monitor:smart")
async def callback_monitor_smart(callback: CallbackQuery):
    """Handle disk SMART monitoring callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading SMART status...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "monitor:smart")
    
    try:
        # Check multiple common disk devices
        devices = ["/dev/sda", "/dev/sdb", "/dev/nvme0n1"]
        smart_data = []
        
        for device in devices:
            output = await _ssh.get_smart_status(device)
            if output:
                smart_data.append((device, output))
        
        if not smart_data:
            await callback.message.edit_text(
                "⚠️ *Disk SMART Status*\n\n"
                "No SMART\\-capable disks found or smartmontools not installed\\.\n\n"
                "_Install with: `apt install smartmontools`_",
                reply_markup=get_back_button("menu:monitoring"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Format output
        messages = ["💾 *Disk SMART Status*\n"]
        
        for device, output in smart_data:
            messages.append(f"\n*{escape_markdown(device)}*")
            
            # Extract key information
            lines = output.split('\n')
            for line in lines:
                if 'SMART overall-health' in line or 'PASSED' in line or 'FAILED' in line:
                    if 'PASSED' in line:
                        messages.append("✅ Health: PASSED")
                    elif 'FAILED' in line:
                        messages.append("❌ Health: FAILED")
                    else:
                        messages.append(escape_markdown(line.strip()))
        
        text = "\n".join(messages)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("menu:monitoring"),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get SMART status: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve SMART status: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:monitoring"),
            parse_mode="MarkdownV2"
        )


@router.callback_query(F.data == "monitor:network")
async def callback_monitor_network(callback: CallbackQuery):
    """Handle network monitoring callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading network stats...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "monitor:network")
    
    try:
        net_output = await _ssh.get_network_stats("all")
        
        if not net_output:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "Failed to retrieve network statistics\\.",
                reply_markup=get_back_button("menu:monitoring"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Parse and format output
        messages = ["🌐 *Network Statistics*\n"]
        
        lines = net_output.split('\n')
        current_interface = None
        
        for line in lines:
            if ':' in line and 'state' in line.lower():
                # Interface line
                parts = line.split(':')
                if len(parts) >= 2:
                    current_interface = parts[1].strip().split()[0]
                    messages.append(f"\n*{escape_markdown(current_interface)}*")
            elif 'RX:' in line and current_interface:
                # Receive stats
                parts = line.strip().split()
                if len(parts) >= 3:
                    rx_bytes = parts[2] if len(parts) > 2 else "0"
                    messages.append(f"📥 RX: {escape_markdown(format_bytes(int(rx_bytes)))}")
            elif 'TX:' in line and current_interface:
                # Transmit stats
                parts = line.strip().split()
                if len(parts) >= 3:
                    tx_bytes = parts[2] if len(parts) > 2 else "0"
                    messages.append(f"📤 TX: {escape_markdown(format_bytes(int(tx_bytes)))}")
        
        text = "\n".join(messages) if len(messages) > 1 else "🌐 *Network Statistics*\n\nNo network data available\\."
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("menu:monitoring"),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get network stats: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve network stats: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:monitoring"),
            parse_mode="MarkdownV2"
        )


@router.callback_query(F.data == "monitor:load")
async def callback_monitor_load(callback: CallbackQuery):
    """Handle load average monitoring callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading system load...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "monitor:load")
    
    try:
        # Get node status which includes load average
        nodes = await _proxmox.get_nodes()
        
        if not nodes:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "No nodes found\\.",
                reply_markup=get_back_button("menu:monitoring"),
                parse_mode="MarkdownV2"
            )
            return
        
        messages = ["📊 *System Load Average*\n"]
        
        for node in nodes:
            node_name = node.get('node', 'unknown')
            
            try:
                status = await _proxmox.get_node_status(node_name)
                
                loadavg = status.get('loadavg', [0, 0, 0])
                load_1 = loadavg[0] if len(loadavg) > 0 else 0
                load_5 = loadavg[1] if len(loadavg) > 1 else 0
                load_15 = loadavg[2] if len(loadavg) > 2 else 0
                
                cpus = status.get('cpuinfo', {}).get('cpus', 1)
                
                messages.append(f"\n📍 *{escape_markdown(node_name)}*")
                messages.append(f"*CPUs:* {cpus}")
                messages.append(f"*Load \\(1m\\):* {load_1:.2f}")
                messages.append(f"*Load \\(5m\\):* {load_5:.2f}")
                messages.append(f"*Load \\(15m\\):* {load_15:.2f}")
                
                # Load per CPU
                load_per_cpu = load_1 / cpus if cpus > 0 else 0
                if load_per_cpu > 1.0:
                    messages.append(f"⚠️ High load: {load_per_cpu:.2f} per CPU")
                else:
                    messages.append(f"✅ Normal load: {load_per_cpu:.2f} per CPU")
                
            except Exception as e:
                logger.error(f"Failed to get load for node {node_name}: {e}")
                messages.append(f"\n📍 *{escape_markdown(node_name)}*")
                messages.append(f"⚠️ Failed to get load: {escape_markdown(str(e))}")
        
        text = "\n".join(messages)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("menu:monitoring"),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get load average: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve load average: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:monitoring"),
            parse_mode="MarkdownV2"
        )
