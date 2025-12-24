"""System logs handler."""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.config import Config
from src.database import Database
from src.services.ssh_client import SSHClient
from src.keyboards.inline import get_logs_keyboard, get_back_button
from src.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

router = Router()

# Global state for dependency injection
_config: Config = None
_db: Database = None
_ssh: SSHClient = None


def setup_logs_router(config: Config, db: Database, ssh: SSHClient):
    """Setup logs router with dependencies.
    
    Args:
        config: Application configuration.
        db: Database instance.
        ssh: SSH client instance.
    """
    global _config, _db, _ssh
    _config = config
    _db = db
    _ssh = ssh


@router.callback_query(F.data == "menu:logs")
async def callback_logs_menu(callback: CallbackQuery):
    """Handle logs menu callback.
    
    Args:
        callback: Callback query.
    """
    await _db.log_command(callback.from_user.id, callback.from_user.username, "logs:menu")
    
    await callback.message.edit_text(
        "📜 *System Logs*\n\n"
        "Select log type:",
        reply_markup=get_logs_keyboard(),
        parse_mode="MarkdownV2"
    )
    await callback.answer()


@router.callback_query(F.data == "logs:system")
async def callback_logs_system(callback: CallbackQuery):
    """Handle system logs callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading system logs...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "logs:system")
    
    try:
        # Get system logs
        logs = await _ssh.get_system_logs(lines=30)
        
        if not logs:
            await callback.message.edit_text(
                "⚠️ *System Logs*\n\n"
                "Failed to retrieve system logs\\.",
                reply_markup=get_back_button("menu:logs"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Truncate if too long (Telegram message limit is 4096 characters)
        max_length = 3500
        if len(logs) > max_length:
            logs = logs[-max_length:]
            logs = "...\n" + logs
        
        # Escape for MarkdownV2
        escaped_logs = escape_markdown(logs.strip())
        
        text = (
            "📋 *System Logs \\(Last 30 Lines\\)*\n\n"
            f"```\n{escaped_logs}\n```"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("menu:logs"),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get system logs: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve system logs: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:logs"),
            parse_mode="MarkdownV2"
        )


@router.callback_query(F.data == "logs:proxmox")
async def callback_logs_proxmox(callback: CallbackQuery):
    """Handle Proxmox logs callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading Proxmox logs...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "logs:proxmox")
    
    try:
        # Get Proxmox service logs
        logs = await _ssh.get_system_logs(lines=30, service="pveproxy")
        
        if not logs:
            # Try alternative service names
            logs = await _ssh.get_system_logs(lines=30, service="pve-cluster")
        
        if not logs:
            await callback.message.edit_text(
                "⚠️ *Proxmox Logs*\n\n"
                "Failed to retrieve Proxmox logs\\.",
                reply_markup=get_back_button("menu:logs"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Truncate if too long
        max_length = 3500
        if len(logs) > max_length:
            logs = logs[-max_length:]
            logs = "...\n" + logs
        
        # Escape for MarkdownV2
        escaped_logs = escape_markdown(logs.strip())
        
        text = (
            "📄 *Proxmox Logs \\(Last 30 Lines\\)*\n\n"
            f"```\n{escaped_logs}\n```"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("menu:logs"),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get Proxmox logs: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve Proxmox logs: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:logs"),
            parse_mode="MarkdownV2"
        )


@router.callback_query(F.data == "logs:qemu")
async def callback_logs_qemu(callback: CallbackQuery):
    """Handle QEMU logs callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading QEMU logs...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "logs:qemu")
    
    try:
        # Get QEMU guest agent logs
        logs = await _ssh.get_system_logs(lines=30, service="qemu-guest-agent")
        
        if not logs:
            await callback.message.edit_text(
                "⚠️ *QEMU Guest Agent Logs*\n\n"
                "Failed to retrieve QEMU logs or service not active\\.",
                reply_markup=get_back_button("menu:logs"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Truncate if too long
        max_length = 3500
        if len(logs) > max_length:
            logs = logs[-max_length:]
            logs = "...\n" + logs
        
        # Escape for MarkdownV2
        escaped_logs = escape_markdown(logs.strip())
        
        text = (
            "🖥️ *QEMU Guest Agent Logs \\(Last 30 Lines\\)*\n\n"
            f"```\n{escaped_logs}\n```"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("menu:logs"),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get QEMU logs: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve QEMU logs: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:logs"),
            parse_mode="MarkdownV2"
        )
