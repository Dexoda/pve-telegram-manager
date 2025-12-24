"""Logs handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
import logging

from src.keyboards.inline import logs_menu, back_button
from src.utils.formatters import format_pre, escape_markdown_v2

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "menu_logs")
async def show_logs_menu(callback: CallbackQuery, db) -> None:
    """Show logs menu."""
    try:
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="menu_logs"
        )
        
        await callback.message.edit_text(
            "📝 *System Logs*\n\nSelect log type:",
            reply_markup=logs_menu(),
            parse_mode="MarkdownV2"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing logs menu: {e}")
        await callback.answer("Error", show_alert=True)


@router.callback_query(F.data == "logs_system")
async def show_system_logs(callback: CallbackQuery, ssh_client, db) -> None:
    """Show system logs."""
    try:
        await callback.answer("Loading logs...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="logs_system"
        )
        
        if not ssh_client:
            await callback.message.edit_text(
                "❌ SSH client not configured\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        logs = await ssh_client.get_system_logs(50)
        
        text = "📋 *System Logs* \\(last 50 lines\\)\n\n"
        text += format_pre(logs[:3500])
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_logs"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing system logs: {e}", exc_info=True)
        await callback.answer("Error loading logs", show_alert=True)


@router.callback_query(F.data == "logs_proxmox")
async def show_proxmox_logs(callback: CallbackQuery, ssh_client, db) -> None:
    """Show Proxmox logs."""
    try:
        await callback.answer("Loading logs...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="logs_proxmox"
        )
        
        if not ssh_client:
            await callback.message.edit_text(
                "❌ SSH client not configured\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        # Get Proxmox logs
        stdout, stderr, exit_code = await ssh_client.run_command(
            "tail -n 50 /var/log/pve/tasks/index"
        )
        
        text = "🖥️ *Proxmox Logs* \\(last 50 lines\\)\n\n"
        
        if exit_code == 0:
            text += format_pre(stdout[:3500])
        else:
            text += f"Error: {escape_markdown_v2(stderr)}"
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_logs"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing Proxmox logs: {e}", exc_info=True)
        await callback.answer("Error loading logs", show_alert=True)


@router.callback_query(F.data == "logs_qemu")
async def show_qemu_logs(callback: CallbackQuery, ssh_client, db) -> None:
    """Show QEMU logs."""
    try:
        await callback.answer("Loading logs...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="logs_qemu"
        )
        
        if not ssh_client:
            await callback.message.edit_text(
                "❌ SSH client not configured\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        # Get QEMU logs via journalctl
        stdout, stderr, exit_code = await ssh_client.run_command(
            "journalctl -u pve-cluster -n 50 --no-pager"
        )
        
        text = "🔧 *QEMU/PVE Logs* \\(last 50 lines\\)\n\n"
        
        if exit_code == 0:
            text += format_pre(stdout[:3500])
        else:
            text += f"Error: {escape_markdown_v2(stderr)}"
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_logs"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing QEMU logs: {e}", exc_info=True)
        await callback.answer("Error loading logs", show_alert=True)


@router.callback_query(F.data == "logs_commands")
async def show_command_logs(callback: CallbackQuery, db) -> None:
    """Show bot command logs."""
    try:
        await callback.answer("Loading logs...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="logs_commands"
        )
        
        # Get command logs
        logs = await db.get_command_logs(limit=20)
        
        text = "📝 *Bot Command Logs* \\(last 20\\)\n\n"
        
        if not logs:
            text += "No command logs found\\."
        else:
            for log in logs:
                username = log.get('username', 'Unknown')
                command = log.get('command', 'unknown')
                timestamp = log.get('timestamp', '')
                
                text += f"• {escape_markdown_v2(str(timestamp)[:19])}\n"
                text += f"  User: @{escape_markdown_v2(username if username else 'N/A')}\n"
                text += f"  Command: `{escape_markdown_v2(command)}`\n\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_logs"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing command logs: {e}", exc_info=True)
        await callback.answer("Error loading logs", show_alert=True)
