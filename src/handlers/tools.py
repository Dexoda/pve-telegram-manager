"""System tools handler - ping, traceroute, updates."""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.config import Config
from src.database import Database
from src.services.ssh_client import SSHClient
from src.keyboards.inline import get_tools_keyboard, get_back_button, InlineKeyboardMarkup, InlineKeyboardButton
from src.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

router = Router()

# Global state for dependency injection
_config: Config = None
_db: Database = None
_ssh: SSHClient = None


class ToolsStates(StatesGroup):
    """States for tools flow."""
    waiting_for_ping_host = State()
    waiting_for_traceroute_host = State()


def setup_tools_router(config: Config, db: Database, ssh: SSHClient):
    """Setup tools router with dependencies.
    
    Args:
        config: Application configuration.
        db: Database instance.
        ssh: SSH client instance.
    """
    global _config, _db, _ssh
    _config = config
    _db = db
    _ssh = ssh


@router.callback_query(F.data == "menu:tools")
async def callback_tools_menu(callback: CallbackQuery):
    """Handle tools menu callback.
    
    Args:
        callback: Callback query.
    """
    await _db.log_command(callback.from_user.id, callback.from_user.username, "tools:menu")
    
    await callback.message.edit_text(
        "🔧 *System Tools*\n\n"
        "Select a tool:",
        reply_markup=get_tools_keyboard(),
        parse_mode="MarkdownV2"
    )
    await callback.answer()


@router.callback_query(F.data == "tools:ping")
async def callback_tools_ping(callback: CallbackQuery, state: FSMContext):
    """Handle ping tool callback.
    
    Args:
        callback: Callback query.
        state: FSM context.
    """
    await _db.log_command(callback.from_user.id, callback.from_user.username, "tools:ping")
    
    await callback.message.edit_text(
        "🏓 *Ping Tool*\n\n"
        "Please enter the hostname or IP address to ping:",
        reply_markup=get_back_button("menu:tools"),
        parse_mode="MarkdownV2"
    )
    
    # Set state to wait for input
    await state.set_state(ToolsStates.waiting_for_ping_host)
    await callback.answer()


@router.message(ToolsStates.waiting_for_ping_host)
async def process_ping_host(message: Message, state: FSMContext):
    """Process ping host input.
    
    Args:
        message: Telegram message.
        state: FSM context.
    """
    host = message.text.strip()
    
    if not host:
        await message.answer(
            "⚠️ Please enter a valid hostname or IP address\\.",
            parse_mode="MarkdownV2"
        )
        return
    
    await message.answer(
        f"🏓 Pinging {escape_markdown(host)}\\.\\.\\.",
        parse_mode="MarkdownV2"
    )
    
    try:
        # Ping host
        output, success = await _ssh.ping_host(host, count=4)
        
        # Truncate if too long
        max_length = 3000
        if len(output) > max_length:
            output = output[:max_length] + "\n..."
        
        # Escape for MarkdownV2
        escaped_output = escape_markdown(output.strip())
        
        status_emoji = "✅" if success else "❌"
        status_text = "Success" if success else "Failed"
        
        text = (
            f"{status_emoji} *Ping Result \\- {escape_markdown(status_text)}*\n\n"
            f"*Host:* {escape_markdown(host)}\n\n"
            f"```\n{escaped_output}\n```"
        )
        
        await message.answer(
            text,
            reply_markup=get_back_button("menu:tools"),
            parse_mode="MarkdownV2"
        )
        
        # Log command
        await _db.log_command(message.from_user.id, message.from_user.username, f"tools:ping:{host}")
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        logger.error(f"Failed to ping host: {e}")
        await message.answer(
            "❌ *Error*\n\n"
            f"Failed to ping host: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:tools"),
            parse_mode="MarkdownV2"
        )
        await state.clear()


@router.callback_query(F.data == "tools:traceroute")
async def callback_tools_traceroute(callback: CallbackQuery, state: FSMContext):
    """Handle traceroute tool callback.
    
    Args:
        callback: Callback query.
        state: FSM context.
    """
    await _db.log_command(callback.from_user.id, callback.from_user.username, "tools:traceroute")
    
    await callback.message.edit_text(
        "🛣️ *Traceroute Tool*\n\n"
        "Please enter the hostname or IP address to traceroute:",
        reply_markup=get_back_button("menu:tools"),
        parse_mode="MarkdownV2"
    )
    
    # Set state to wait for input
    await state.set_state(ToolsStates.waiting_for_traceroute_host)
    await callback.answer()


@router.message(ToolsStates.waiting_for_traceroute_host)
async def process_traceroute_host(message: Message, state: FSMContext):
    """Process traceroute host input.
    
    Args:
        message: Telegram message.
        state: FSM context.
    """
    host = message.text.strip()
    
    if not host:
        await message.answer(
            "⚠️ Please enter a valid hostname or IP address\\.",
            parse_mode="MarkdownV2"
        )
        return
    
    await message.answer(
        f"🛣️ Traceroute to {escape_markdown(host)}\\.\\.\\.\n\n"
        "_This may take up to 60 seconds\\._",
        parse_mode="MarkdownV2"
    )
    
    try:
        # Traceroute host
        output, success = await _ssh.traceroute_host(host, max_hops=30)
        
        # Truncate if too long
        max_length = 3000
        if len(output) > max_length:
            output = output[:max_length] + "\n..."
        
        # Escape for MarkdownV2
        escaped_output = escape_markdown(output.strip())
        
        status_emoji = "✅" if success else "❌"
        status_text = "Completed" if success else "Failed"
        
        text = (
            f"{status_emoji} *Traceroute Result \\- {escape_markdown(status_text)}*\n\n"
            f"*Host:* {escape_markdown(host)}\n\n"
            f"```\n{escaped_output}\n```"
        )
        
        await message.answer(
            text,
            reply_markup=get_back_button("menu:tools"),
            parse_mode="MarkdownV2"
        )
        
        # Log command
        await _db.log_command(message.from_user.id, message.from_user.username, f"tools:traceroute:{host}")
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        logger.error(f"Failed to traceroute host: {e}")
        await message.answer(
            "❌ *Error*\n\n"
            f"Failed to traceroute host: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:tools"),
            parse_mode="MarkdownV2"
        )
        await state.clear()


@router.callback_query(F.data == "tools:update")
async def callback_tools_update(callback: CallbackQuery):
    """Handle system update callback.
    
    Args:
        callback: Callback query.
    """
    await _db.log_command(callback.from_user.id, callback.from_user.username, "tools:update:prompt")
    
    # Create confirmation keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yes, Update", callback_data="tools:update:confirm"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="menu:tools")
        ]
    ])
    
    await callback.message.edit_text(
        "🔄 *System Update*\n\n"
        "⚠️ *Warning:* This will update all system packages\\.\n\n"
        "The update process may take several minutes and will run:\n"
        "```\napt-get update && apt-get upgrade -y\n```\n\n"
        "Do you want to proceed?",
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
    await callback.answer()


@router.callback_query(F.data == "tools:update:confirm")
async def callback_tools_update_confirm(callback: CallbackQuery):
    """Handle system update confirmation callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Starting system update...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "tools:update:execute")
    
    await callback.message.edit_text(
        "🔄 *System Update*\n\n"
        "Updating system packages\\.\\.\\.\n\n"
        "_This may take several minutes\\. Please wait\\._",
        parse_mode="MarkdownV2"
    )
    
    try:
        # Run system update
        success, output = await _ssh.update_system()
        
        # Truncate output if too long
        max_length = 2500
        if len(output) > max_length:
            output = output[-max_length:]
            output = "...\n" + output
        
        # Escape for MarkdownV2
        escaped_output = escape_markdown(output.strip())
        
        if success:
            text = (
                "✅ *System Update Completed*\n\n"
                f"```\n{escaped_output}\n```"
            )
        else:
            text = (
                "❌ *System Update Failed*\n\n"
                f"```\n{escaped_output}\n```"
            )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("menu:tools"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Failed to update system: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to update system: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:tools"),
            parse_mode="MarkdownV2"
        )
