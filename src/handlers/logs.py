"""
Logs handlers for system and Proxmox logs.
"""
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.services.ssh_client import SSHClient
from src.database.db import Database
from src.keyboards.inline import get_back_keyboard
from src.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

router = Router()

# Global instances (will be set in main.py)
ssh_client: Optional[SSHClient] = None
db: Optional[Database] = None


def set_services(ssh: SSHClient, database: Database) -> None:
    """Set global service instances."""
    global ssh_client, db
    ssh_client = ssh
    db = database


def get_logs_menu_keyboard() -> InlineKeyboardMarkup:
    """Get logs menu keyboard."""
    buttons = [
        [InlineKeyboardButton(text="📋 System Logs", callback_data="logs_system")],
        [InlineKeyboardButton(text="🖥 Proxmox Logs", callback_data="logs_proxmox")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "menu_logs")
async def menu_logs(callback: CallbackQuery) -> None:
    """
    Handle logs menu callback.
    
    Args:
        callback: Callback query object
    """
    text = (
        "📋 *Logs*\n\n"
        "Select which logs to view:"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=get_logs_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "logs_system")
async def logs_system(callback: CallbackQuery) -> None:
    """
    Handle system logs callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Loading system logs...")
    
    try:
        if not ssh_client:
            await callback.answer("SSH client not available", show_alert=True)
            return
        
        # Get system logs
        logs = await ssh_client.get_system_logs(lines=30)
        
        if not logs:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "Failed to retrieve system logs\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_logs")
            )
            return
        
        # Format logs (limit length for Telegram)
        log_lines = logs.strip().split('\n')
        
        # Take last 20 lines if too long
        if len(log_lines) > 20:
            log_lines = log_lines[-20:]
        
        # Escape and format
        formatted_logs = []
        for line in log_lines:
            # Truncate very long lines
            if len(line) > 100:
                line = line[:97] + "..."
            formatted_logs.append(escape_markdown(line))
        
        text = "📋 *System Logs* \\(last 20 entries\\)\n\n"
        text += "```\n"
        text += "\n".join(formatted_logs)
        text += "\n```"
        
        # Log action
        if db:
            await db.log_command(
                callback.from_user.id,
                callback.from_user.username,
                "logs_system"
            )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_logs")
        )
        
    except Exception as e:
        logger.error(f"Error getting system logs: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to get system logs: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_logs")
        )


@router.callback_query(F.data == "logs_proxmox")
async def logs_proxmox(callback: CallbackQuery) -> None:
    """
    Handle Proxmox logs callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Loading Proxmox logs...")
    
    try:
        if not ssh_client:
            await callback.answer("SSH client not available", show_alert=True)
            return
        
        # Get Proxmox logs
        logs = await ssh_client.get_proxmox_logs(lines=30)
        
        if not logs:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "Failed to retrieve Proxmox logs\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_logs")
            )
            return
        
        # Format logs (limit length for Telegram)
        log_lines = logs.strip().split('\n')
        
        # Take last 20 lines if too long
        if len(log_lines) > 20:
            log_lines = log_lines[-20:]
        
        # Escape and format
        formatted_logs = []
        for line in log_lines:
            # Truncate very long lines
            if len(line) > 100:
                line = line[:97] + "..."
            formatted_logs.append(escape_markdown(line))
        
        text = "🖥 *Proxmox Logs* \\(last 20 entries\\)\n\n"
        text += "```\n"
        text += "\n".join(formatted_logs)
        text += "\n```"
        
        # Log action
        if db:
            await db.log_command(
                callback.from_user.id,
                callback.from_user.username,
                "logs_proxmox"
            )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_logs")
        )
        
    except Exception as e:
        logger.error(f"Error getting Proxmox logs: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to get Proxmox logs: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_logs")
        )
