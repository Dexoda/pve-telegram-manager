"""Common handlers: /start, /help, main menu, and authorization middleware."""

import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.config import Config
from src.database import Database
from src.keyboards.inline import get_main_menu_keyboard
from src.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

router = Router()


# Global state for dependency injection
_config: Config = None
_db: Database = None


def setup_common_router(config: Config, db: Database):
    """Setup common router with dependencies.
    
    Args:
        config: Application configuration.
        db: Database instance.
    """
    global _config, _db
    _config = config
    _db = db


def admin_required(func: Callable) -> Callable:
    """Middleware to check if user is admin.
    
    Args:
        func: Handler function to wrap.
        
    Returns:
        Callable: Wrapped handler function.
    """
    async def wrapper(event: Message | CallbackQuery, *args, **kwargs):
        user_id = event.from_user.id
        
        if user_id not in _config.telegram.admin_ids:
            logger.warning(f"Unauthorized access attempt from user {user_id}")
            
            if isinstance(event, Message):
                await event.answer(
                    "🚫 *Access Denied*\n\n"
                    "You are not authorized to use this bot\\.",
                    parse_mode="MarkdownV2"
                )
            else:
                await event.answer("🚫 Access denied", show_alert=True)
            
            return
        
        # Update user in database
        username = event.from_user.username
        await _db.update_user(user_id, username)
        
        return await func(event, *args, **kwargs)
    
    return wrapper


@router.message(Command("start"))
@admin_required
async def cmd_start(message: Message):
    """Handle /start command.
    
    Args:
        message: Telegram message.
    """
    await _db.log_command(message.from_user.id, message.from_user.username, "/start")
    
    welcome_text = (
        "🤖 *Proxmox VE Telegram Manager*\n\n"
        "Welcome to your Proxmox management bot\\!\n\n"
        "*Available Features:*\n"
        "🖥️ Virtual Machine Management\n"
        "📊 System Monitoring\n"
        "💾 Storage Management\n"
        "⚡ Electricity Cost Calculator\n"
        "📜 System Logs\n"
        "🔧 Utilities\n\n"
        "Use the menu below to get started\\."
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="MarkdownV2"
    )


@router.message(Command("help"))
@admin_required
async def cmd_help(message: Message):
    """Handle /help command.
    
    Args:
        message: Telegram message.
    """
    await _db.log_command(message.from_user.id, message.from_user.username, "/help")
    
    help_text = (
        "📖 *Help \\- Proxmox VE Manager*\n\n"
        "*Main Commands:*\n"
        "/start \\- Show main menu\n"
        "/help \\- Show this help message\n\n"
        "*Features:*\n\n"
        "🖥️ *Virtual Machines*\n"
        "• View all VMs and containers\n"
        "• Start, stop, reboot VMs\n"
        "• View VM details and status\n"
        "• Add VMs to favorites\n"
        "• Access NoVNC console\n\n"
        "📊 *Monitoring*\n"
        "• Node resource usage\n"
        "• CPU temperature\n"
        "• Disk SMART status\n"
        "• Network statistics\n"
        "• System load average\n\n"
        "💾 *Storage*\n"
        "• Browse ISO images\n"
        "• Download new ISOs\n"
        "• View storage pools\n"
        "• Browse backups\n\n"
        "⚡ *Finance*\n"
        "• Calculate electricity costs\n"
        "• Almaty progressive tariffs\n\n"
        "📜 *Logs*\n"
        "• System logs\n"
        "• Proxmox logs\n"
        "• QEMU logs\n\n"
        "🔧 *Tools*\n"
        "• Ping hosts\n"
        "• Traceroute\n"
        "• System updates\n\n"
        "For support, contact @Dexoda"
    )
    
    await message.answer(
        help_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="MarkdownV2"
    )


@router.callback_query(F.data == "menu:main")
@admin_required
async def callback_main_menu(callback: CallbackQuery):
    """Handle main menu callback.
    
    Args:
        callback: Callback query.
    """
    await callback.message.edit_text(
        "🏠 *Main Menu*\n\n"
        "Select an option:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="MarkdownV2"
    )
    await callback.answer()


@router.callback_query(F.data == "menu:vms")
@admin_required
async def callback_vms_menu(callback: CallbackQuery):
    """Handle VMs menu callback.
    
    Args:
        callback: Callback query.
    """
    # This will be handled by vms.py router
    await callback.answer()


@router.callback_query(F.data == "menu:monitoring")
@admin_required
async def callback_monitoring_menu(callback: CallbackQuery):
    """Handle monitoring menu callback.
    
    Args:
        callback: Callback query.
    """
    # This will be handled by monitoring.py router
    await callback.answer()


@router.callback_query(F.data == "menu:storage")
@admin_required
async def callback_storage_menu(callback: CallbackQuery):
    """Handle storage menu callback.
    
    Args:
        callback: Callback query.
    """
    # This will be handled by storage.py router
    await callback.answer()


@router.callback_query(F.data.startswith("menu:"))
@admin_required
async def callback_other_menus(callback: CallbackQuery):
    """Handle other menu callbacks (placeholder).
    
    Args:
        callback: Callback query.
    """
    menu_type = callback.data.split(":")[1]
    
    menu_messages = {
        "finance": "⚡ *Finance*\n\nFinance calculator coming soon\\!",
        "logs": "📜 *Logs*\n\nLog viewer coming soon\\!",
        "tools": "🔧 *Tools*\n\nUtilities coming soon\\!",
    }
    
    text = menu_messages.get(menu_type, "Feature coming soon\\!")
    
    from src.keyboards.inline import get_back_button
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_button("menu:main"),
        parse_mode="MarkdownV2"
    )
    await callback.answer()
