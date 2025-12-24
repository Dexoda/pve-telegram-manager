"""Common handlers and middleware."""
from typing import Callable, Dict, Any, Awaitable
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramAPIError
import logging

from src.keyboards.inline import main_menu
from src.utils.formatters import escape_markdown_v2

logger = logging.getLogger(__name__)

router = Router()


async def check_admin(handler: Callable, event, data: Dict[str, Any]) -> Any:
    """
    Middleware to check if user is admin.
    
    Args:
        handler: Handler function
        event: Event (Message or CallbackQuery)
        data: Handler data
        
    Returns:
        Handler result or None
    """
    config = data.get("config")
    db = data.get("db")
    
    # Get user from event
    if isinstance(event, Message):
        user = event.from_user
        chat_id = event.chat.id
    elif isinstance(event, CallbackQuery):
        user = event.from_user
        chat_id = event.message.chat.id if event.message else user.id
    else:
        return await handler(event, data)
    
    # Log user activity
    await db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Check if user is admin
    if user.id not in config.ADMIN_IDS:
        error_msg = (
            "🚫 *Access Denied*\n\n"
            "You are not authorized to use this bot\\.\n"
            f"Your User ID: `{user.id}`"
        )
        
        if isinstance(event, Message):
            await event.answer(error_msg, parse_mode="MarkdownV2")
        elif isinstance(event, CallbackQuery):
            await event.answer("Access denied", show_alert=True)
        
        logger.warning(f"Unauthorized access attempt by {user.id} (@{user.username})")
        return None
    
    # User is admin, continue
    return await handler(event, data)


# Register middleware
router.message.middleware(check_admin)
router.callback_query.middleware(check_admin)


@router.message(Command("start"))
async def cmd_start(message: Message, db, config) -> None:
    """
    Handle /start command.
    
    Args:
        message: Message object
        db: Database instance
        config: Config instance
    """
    try:
        user = message.from_user
        
        # Log command
        await db.log_command(
            user_id=user.id,
            username=user.username,
            command="/start"
        )
        
        welcome_text = (
            "🖥️ *Welcome to PVE Telegram Manager\\!*\n\n"
            "This bot allows you to manage your Proxmox VE server directly from Telegram\\.\n\n"
            "*Available features:*\n"
            "• Manage Virtual Machines\n"
            "• Monitor system resources\n"
            "• Manage storage and ISO images\n"
            "• View system logs\n"
            "• Use system tools\n"
            "• Calculate electricity costs\n\n"
            "Use the buttons below to navigate\\."
        )
        
        await message.answer(
            welcome_text,
            reply_markup=main_menu(),
            parse_mode="MarkdownV2"
        )
        
        logger.info(f"User {user.id} (@{user.username}) started the bot")
    except Exception as e:
        logger.error(f"Error in /start command: {e}", exc_info=True)
        await message.answer("An error occurred. Please try again later.")


@router.message(Command("help"))
async def cmd_help(message: Message, db) -> None:
    """
    Handle /help command.
    
    Args:
        message: Message object
        db: Database instance
    """
    try:
        user = message.from_user
        
        # Log command
        await db.log_command(
            user_id=user.id,
            username=user.username,
            command="/help"
        )
        
        help_text = (
            "📖 *Bot Commands Help*\n\n"
            "*Basic Commands:*\n"
            "`/start` \\- Start the bot and show main menu\n"
            "`/help` \\- Show this help message\n"
            "`/vms` \\- List all virtual machines\n"
            "`/favorites` \\- Show favorite VMs\n\n"
            "*Main Menu Sections:*\n"
            "🖥️ *Virtual Machines* \\- Manage VMs and containers\n"
            "📊 *Monitoring* \\- System resources monitoring\n"
            "💾 *Storage* \\- Manage storage and ISO images\n"
            "🛠️ *Tools* \\- System utilities\n"
            "📝 *Logs* \\- View system logs\n"
            "💰 *Finance* \\- Electricity cost calculator\n\n"
            "*VM Management:*\n"
            "• View VM list with status\n"
            "• Start/Stop/Reboot VMs\n"
            "• View VM details\n"
            "• Add VMs to favorites\n"
            "• Access NoVNC console\n\n"
            "*Monitoring:*\n"
            "• CPU and RAM usage\n"
            "• CPU temperature\n"
            "• SMART disk status\n"
            "• Network statistics\n"
            "• Load average\n\n"
            "For more information, visit the documentation\\."
        )
        
        await message.answer(
            help_text,
            parse_mode="MarkdownV2"
        )
        
        logger.info(f"User {user.id} requested help")
    except Exception as e:
        logger.error(f"Error in /help command: {e}", exc_info=True)
        await message.answer("An error occurred. Please try again later.")


@router.callback_query(F.data == "menu_main")
async def callback_main_menu(callback: CallbackQuery) -> None:
    """
    Handle main menu callback.
    
    Args:
        callback: CallbackQuery object
    """
    try:
        await callback.message.edit_text(
            "🏠 *Main Menu*\n\nSelect an option:",
            reply_markup=main_menu(),
            parse_mode="MarkdownV2"
        )
        await callback.answer()
    except TelegramAPIError as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error showing main menu: {e}")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in main menu callback: {e}", exc_info=True)
        await callback.answer("An error occurred")


@router.callback_query(F.data == "cancel")
async def callback_cancel(callback: CallbackQuery) -> None:
    """
    Handle cancel callback.
    
    Args:
        callback: CallbackQuery object
    """
    try:
        await callback.message.edit_text(
            "❌ *Operation Cancelled*",
            parse_mode="MarkdownV2"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in cancel callback: {e}")
        await callback.answer()
