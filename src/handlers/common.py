"""
Common handlers: /start, /help, main menu, and authorization middleware.
"""
import logging
from typing import Optional, Callable, Dict, Any, Awaitable
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.types import TelegramObject

from src.config import config
from src.database.db import Database
from src.keyboards.inline import get_main_menu_keyboard
from src.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

router = Router()

# Global database instance (will be set in main.py)
db: Optional[Database] = None


def set_database(database: Database) -> None:
    """Set global database instance."""
    global db
    db = database


async def admin_middleware(
    handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: Dict[str, Any]
) -> Any:
    """
    Middleware to check if user is admin.
    
    Args:
        handler: Next handler
        event: Event object
        data: Handler data
        
    Returns:
        Handler result or None if not authorized
    """
    # Get user ID from message or callback query
    user_id = None
    username = None
    
    if isinstance(event, Message):
        user_id = event.from_user.id
        username = event.from_user.username
    elif isinstance(event, CallbackQuery):
        user_id = event.from_user.id
        username = event.from_user.username
    
    if user_id is None:
        return None
    
    # Check if user is admin
    if user_id not in config.ADMIN_IDS:
        logger.warning(f"Unauthorized access attempt from user {user_id}")
        
        if isinstance(event, Message):
            await event.answer(
                "⛔️ *Access Denied*\n\n"
                "You are not authorized to use this bot\\.\n"
                "Please contact the administrator\\.",
                parse_mode="MarkdownV2"
            )
        elif isinstance(event, CallbackQuery):
            await event.answer("⛔️ Access denied", show_alert=True)
        
        return None
    
    # Log user activity
    if db:
        await db.add_user(user_id, username)
    
    # Continue to handler
    return await handler(event, data)


# Register middleware
router.message.middleware(admin_middleware)
router.callback_query.middleware(admin_middleware)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """
    Handle /start command.
    
    Args:
        message: Message object
    """
    user_name = escape_markdown(message.from_user.first_name or "User")
    
    welcome_text = (
        f"👋 *Welcome, {user_name}\\!*\n\n"
        "🤖 *Proxmox VE Telegram Manager*\n\n"
        "This bot allows you to manage your Proxmox Virtual Environment from Telegram\\.\n\n"
        "🔹 Manage VMs and containers\n"
        "🔹 Monitor system resources\n"
        "🔹 View logs and statistics\n"
        "🔹 Control storage and backups\n"
        "🔹 Execute system tools\n\n"
        "Select an option from the menu below:"
    )
    
    # Log command
    if db:
        await db.log_command(message.from_user.id, message.from_user.username, "/start")
    
    await message.answer(
        welcome_text,
        parse_mode="MarkdownV2",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    Handle /help command.
    
    Args:
        message: Message object
    """
    help_text = (
        "📚 *Help \\- Available Commands*\n\n"
        "*Basic Commands:*\n"
        "/start \\- Show main menu\n"
        "/help \\- Show this help message\n"
        "/menu \\- Show main menu\n\n"
        "*VM Management:*\n"
        "• List all virtual machines\n"
        "• Start/Stop/Reboot VMs\n"
        "• View VM details and status\n"
        "• Add VMs to favorites\n"
        "• Access NoVNC console\n\n"
        "*Monitoring:*\n"
        "• View node status \\(CPU, RAM, Uptime\\)\n"
        "• Check CPU temperature\n"
        "• Monitor disk usage\n"
        "• Check SMART status\n"
        "• View network traffic\n"
        "• Monitor load average\n\n"
        "*Storage:*\n"
        "• List ISO images\n"
        "• Download ISO from URL\n"
        "• View storage usage\n"
        "• List backups\n\n"
        "*Tools:*\n"
        "• Ping hosts\n"
        "• Traceroute\n"
        "• System updates\n\n"
        "*Finance:*\n"
        "• Calculate electricity costs\n\n"
        "*Logs:*\n"
        "• View system logs\n"
        "• View Proxmox logs\n"
        "• View QEMU logs\n\n"
        "💡 Use the inline buttons to navigate through the bot\\."
    )
    
    # Log command
    if db:
        await db.log_command(message.from_user.id, message.from_user.username, "/help")
    
    await message.answer(
        help_text,
        parse_mode="MarkdownV2",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """
    Handle /menu command.
    
    Args:
        message: Message object
    """
    # Log command
    if db:
        await db.log_command(message.from_user.id, message.from_user.username, "/menu")
    
    await message.answer(
        "📋 *Main Menu*\n\nSelect an option:",
        parse_mode="MarkdownV2",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery) -> None:
    """
    Handle main menu callback.
    
    Args:
        callback: Callback query object
    """
    await callback.message.edit_text(
        "📋 *Main Menu*\n\nSelect an option:",
        parse_mode="MarkdownV2",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery) -> None:
    """
    Handle help callback.
    
    Args:
        callback: Callback query object
    """
    help_text = (
        "📚 *Help \\- Available Commands*\n\n"
        "*Basic Commands:*\n"
        "/start \\- Show main menu\n"
        "/help \\- Show this help message\n"
        "/menu \\- Show main menu\n\n"
        "*VM Management:*\n"
        "• List all virtual machines\n"
        "• Start/Stop/Reboot VMs\n"
        "• View VM details and status\n"
        "• Add VMs to favorites\n"
        "• Access NoVNC console\n\n"
        "*Monitoring:*\n"
        "• View node status \\(CPU, RAM, Uptime\\)\n"
        "• Check CPU temperature\n"
        "• Monitor disk usage\n"
        "• Check SMART status\n"
        "• View network traffic\n"
        "• Monitor load average\n\n"
        "*Storage:*\n"
        "• List ISO images\n"
        "• Download ISO from URL\n"
        "• View storage usage\n"
        "• List backups\n\n"
        "*Tools:*\n"
        "• Ping hosts\n"
        "• Traceroute\n"
        "• System updates\n\n"
        "*Finance:*\n"
        "• Calculate electricity costs\n\n"
        "*Logs:*\n"
        "• View system logs\n"
        "• View Proxmox logs\n"
        "• View QEMU logs\n\n"
        "💡 Use the inline buttons to navigate through the bot\\."
    )
    
    await callback.message.edit_text(
        help_text,
        parse_mode="MarkdownV2",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
