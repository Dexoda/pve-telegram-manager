"""Monitoring handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
import logging

from src.keyboards.inline import monitoring_menu, back_button
from src.utils.formatters import escape_markdown_v2, format_pre
from src.utils.progress_bars import format_bytes, create_progress_bar, format_load_average

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "menu_monitoring")
async def show_monitoring_menu(callback: CallbackQuery, db) -> None:
    """Show monitoring menu."""
    try:
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="menu_monitoring"
        )
        
        await callback.message.edit_text(
            "📊 *System Monitoring*\n\nSelect monitoring option:",
            reply_markup=monitoring_menu(),
            parse_mode="MarkdownV2"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing monitoring menu: {e}")
        await callback.answer("Error", show_alert=True)


@router.callback_query(F.data == "mon_cpu_ram")
async def show_cpu_ram(callback: CallbackQuery, proxmox, db) -> None:
    """Show CPU and RAM usage."""
    try:
        await callback.answer("Loading...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="mon_cpu_ram"
        )
        
        nodes = await proxmox.get_nodes()
        
        if not nodes:
            await callback.message.edit_text(
                "No nodes found\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        text = "💻 *CPU \\& RAM Usage*\n\n"
        
        for node_info in nodes:
            node = node_info['node']
            status = await proxmox.get_node_status(node)
            
            text += f"*Node:* {escape_markdown_v2(node)}\n"
            
            # CPU
            if 'cpu' in status:
                cpu_usage = status['cpu'] * 100
                cpu_bar = create_progress_bar(cpu_usage, 100)
                text += f"CPU: {escape_markdown_v2(cpu_bar)}\n"
            
            # Memory
            if 'memory' in status:
                mem_used = status['memory'].get('used', 0)
                mem_total = status['memory'].get('total', 1)
                mem_percent = (mem_used / mem_total * 100) if mem_total > 0 else 0
                mem_bar = create_progress_bar(mem_used, mem_total)
                text += f"RAM: {escape_markdown_v2(mem_bar)}\n"
                text += f"     {escape_markdown_v2(format_bytes(mem_used))} / {escape_markdown_v2(format_bytes(mem_total))}\n"
            
            text += "\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_monitoring"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing CPU/RAM: {e}", exc_info=True)
        await callback.answer("Error loading data", show_alert=True)


@router.callback_query(F.data == "mon_temperature")
async def show_temperature(callback: CallbackQuery, ssh_client, db) -> None:
    """Show CPU temperature."""
    try:
        await callback.answer("Loading...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="mon_temperature"
        )
        
        if not ssh_client:
            await callback.message.edit_text(
                "❌ SSH client not configured\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        temp_output = await ssh_client.get_cpu_temperature()
        
        text = "🌡️ *CPU Temperature*\n\n"
        text += format_pre(temp_output[:3500])  # Limit output
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_monitoring"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing temperature: {e}", exc_info=True)
        await callback.answer("Error loading temperature", show_alert=True)


@router.callback_query(F.data == "mon_load")
async def show_load_average(callback: CallbackQuery, proxmox, db) -> None:
    """Show load average."""
    try:
        await callback.answer("Loading...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="mon_load"
        )
        
        nodes = await proxmox.get_nodes()
        
        text = "📊 *Load Average*\n\n"
        
        for node_info in nodes:
            node = node_info['node']
            status = await proxmox.get_node_status(node)
            
            text += f"*Node:* {escape_markdown_v2(node)}\n"
            
            if 'loadavg' in status:
                load_avg = status['loadavg']
                load_str = format_load_average(load_avg)
                text += f"Load: {escape_markdown_v2(load_str)}\n"
            
            if 'cpuinfo' in status and 'cpus' in status['cpuinfo']:
                cpus = status['cpuinfo']['cpus']
                text += f"CPUs: {cpus}\n"
            
            text += "\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_monitoring"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing load average: {e}", exc_info=True)
        await callback.answer("Error loading data", show_alert=True)


@router.callback_query(F.data == "mon_smart")
async def show_smart_status(callback: CallbackQuery, ssh_client, db) -> None:
    """Show SMART disk status."""
    try:
        await callback.answer("Loading SMART data...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="mon_smart"
        )
        
        if not ssh_client:
            await callback.message.edit_text(
                "❌ SSH client not configured\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        smart_output = await ssh_client.get_smart_status()
        
        text = "💾 *SMART Disk Status*\n\n"
        text += format_pre(smart_output[:3500])  # Limit output
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_monitoring"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing SMART status: {e}", exc_info=True)
        await callback.answer("Error loading SMART data", show_alert=True)


@router.callback_query(F.data == "mon_disks")
async def show_disk_usage(callback: CallbackQuery, ssh_client, db) -> None:
    """Show disk usage."""
    try:
        await callback.answer("Loading...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="mon_disks"
        )
        
        if not ssh_client:
            await callback.message.edit_text(
                "❌ SSH client not configured\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        disk_output = await ssh_client.get_disk_usage()
        
        text = "💿 *Disk Usage*\n\n"
        text += format_pre(disk_output[:3500])
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_monitoring"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing disk usage: {e}", exc_info=True)
        await callback.answer("Error loading disk usage", show_alert=True)


@router.callback_query(F.data == "mon_network")
async def show_network_stats(callback: CallbackQuery, ssh_client, db) -> None:
    """Show network statistics."""
    try:
        await callback.answer("Loading...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="mon_network"
        )
        
        if not ssh_client:
            await callback.message.edit_text(
                "❌ SSH client not configured\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        network_output = await ssh_client.get_network_stats()
        
        text = "📶 *Network Statistics*\n\n"
        text += format_pre(network_output[:3500])
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_monitoring"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing network stats: {e}", exc_info=True)
        await callback.answer("Error loading network stats", show_alert=True)
