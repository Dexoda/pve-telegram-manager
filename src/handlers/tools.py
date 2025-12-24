"""
Tools handlers for utilities like ping, traceroute, and system updates.
"""
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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


class ToolsStates(StatesGroup):
    """States for tools."""
    waiting_for_ping_host = State()
    waiting_for_traceroute_host = State()


def get_tools_menu_keyboard() -> InlineKeyboardMarkup:
    """Get tools menu keyboard."""
    buttons = [
        [InlineKeyboardButton(text="🏓 Ping", callback_data="tools_ping")],
        [InlineKeyboardButton(text="🗺 Traceroute", callback_data="tools_traceroute")],
        [InlineKeyboardButton(text="🔄 System Update", callback_data="tools_update")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "menu_tools")
async def menu_tools(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle tools menu callback.
    
    Args:
        callback: Callback query object
        state: FSM context
    """
    # Clear any existing state
    await state.clear()
    
    text = (
        "🔧 *Tools*\n\n"
        "Select a tool to use:"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=get_tools_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "tools_ping")
async def tools_ping(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle ping tool callback.
    
    Args:
        callback: Callback query object
        state: FSM context
    """
    text = (
        "🏓 *Ping*\n\n"
        "Please send the hostname or IP address to ping\\.\n\n"
        "_Example: google\\.com_"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=get_back_keyboard("menu_tools")
    )
    
    # Set state
    await state.set_state(ToolsStates.waiting_for_ping_host)
    await callback.answer()


@router.message(ToolsStates.waiting_for_ping_host)
async def process_ping(message: Message, state: FSMContext) -> None:
    """
    Process ping host input.
    
    Args:
        message: Message object
        state: FSM context
    """
    host = message.text.strip()
    
    if not host:
        await message.answer(
            "❌ Please enter a valid hostname or IP address\\.",
            parse_mode="MarkdownV2"
        )
        return
    
    # Send "processing" message
    processing_msg = await message.answer(
        f"🏓 Pinging {escape_markdown(host)}\\.\\.\\.",
        parse_mode="MarkdownV2"
    )
    
    try:
        if not ssh_client:
            await processing_msg.edit_text(
                "❌ SSH client not available\\.",
                parse_mode="MarkdownV2"
            )
            await state.clear()
            return
        
        # Execute ping
        success, output = await ssh_client.ping_host(host, count=4)
        
        # Format output
        if success:
            # Extract key information
            lines = output.strip().split('\n')
            
            # Find summary line
            summary = ""
            stats = ""
            for i, line in enumerate(lines):
                if 'packets transmitted' in line.lower():
                    summary = line
                    if i + 1 < len(lines):
                        stats = lines[i + 1]
                    break
            
            text = f"🏓 *Ping Results*\n\n"
            text += f"*Host:* {escape_markdown(host)}\n\n"
            
            if summary:
                text += f"```\n{escape_markdown(summary)}\n"
                if stats:
                    text += f"{escape_markdown(stats)}\n"
                text += "```"
            else:
                # Show full output if summary not found
                output_lines = lines[-10:]  # Last 10 lines
                text += "```\n"
                for line in output_lines:
                    text += f"{escape_markdown(line[:80])}\n"
                text += "```"
        else:
            text = f"❌ *Ping Failed*\n\n"
            text += f"*Host:* {escape_markdown(host)}\n\n"
            text += f"Error: {escape_markdown(output[:200])}"
        
        # Log action
        if db:
            await db.log_command(
                message.from_user.id,
                message.from_user.username,
                f"ping_{host}"
            )
        
        await processing_msg.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_tools")
        )
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error executing ping: {e}")
        await processing_msg.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to ping host: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_tools")
        )
        await state.clear()


@router.callback_query(F.data == "tools_traceroute")
async def tools_traceroute(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle traceroute tool callback.
    
    Args:
        callback: Callback query object
        state: FSM context
    """
    text = (
        "🗺 *Traceroute*\n\n"
        "Please send the hostname or IP address to traceroute\\.\n\n"
        "_Example: google\\.com_"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=get_back_keyboard("menu_tools")
    )
    
    # Set state
    await state.set_state(ToolsStates.waiting_for_traceroute_host)
    await callback.answer()


@router.message(ToolsStates.waiting_for_traceroute_host)
async def process_traceroute(message: Message, state: FSMContext) -> None:
    """
    Process traceroute host input.
    
    Args:
        message: Message object
        state: FSM context
    """
    host = message.text.strip()
    
    if not host:
        await message.answer(
            "❌ Please enter a valid hostname or IP address\\.",
            parse_mode="MarkdownV2"
        )
        return
    
    # Send "processing" message
    processing_msg = await message.answer(
        f"🗺 Traceroute to {escape_markdown(host)}\\.\\.\\.\n\n"
        "_This may take up to 60 seconds\\._",
        parse_mode="MarkdownV2"
    )
    
    try:
        if not ssh_client:
            await processing_msg.edit_text(
                "❌ SSH client not available\\.",
                parse_mode="MarkdownV2"
            )
            await state.clear()
            return
        
        # Execute traceroute
        success, output = await ssh_client.traceroute_host(host, max_hops=15)
        
        # Format output
        if success or output:
            lines = output.strip().split('\n')
            
            # Take first 20 lines
            if len(lines) > 20:
                lines = lines[:20]
                lines.append("... (truncated)")
            
            text = f"🗺 *Traceroute Results*\n\n"
            text += f"*Host:* {escape_markdown(host)}\n\n"
            text += "```\n"
            
            for line in lines:
                # Truncate long lines
                if len(line) > 70:
                    line = line[:67] + "..."
                text += f"{escape_markdown(line)}\n"
            
            text += "```"
        else:
            text = f"❌ *Traceroute Failed*\n\n"
            text += f"*Host:* {escape_markdown(host)}\n\n"
            text += "No output received\\."
        
        # Log action
        if db:
            await db.log_command(
                message.from_user.id,
                message.from_user.username,
                f"traceroute_{host}"
            )
        
        await processing_msg.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_tools")
        )
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error executing traceroute: {e}")
        await processing_msg.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to traceroute host: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_tools")
        )
        await state.clear()


@router.callback_query(F.data == "tools_update")
async def tools_update(callback: CallbackQuery) -> None:
    """
    Handle system update callback.
    
    Args:
        callback: Callback query object
    """
    # Create confirmation keyboard
    buttons = [
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data="tools_update_confirm"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="menu_tools")
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    text = (
        "🔄 *System Update*\n\n"
        "⚠️ *Warning:* This will update all system packages\\.\n\n"
        "This operation may take several minutes and may require a reboot\\.\n\n"
        "Are you sure you want to continue?"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "tools_update_confirm")
async def tools_update_confirm(callback: CallbackQuery) -> None:
    """
    Handle system update confirmation.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Starting system update...")
    
    # Update message
    await callback.message.edit_text(
        "🔄 *System Update*\n\n"
        "Updating system packages\\.\\.\\.\n\n"
        "_This may take several minutes\\. Please wait\\._",
        parse_mode="MarkdownV2"
    )
    
    try:
        if not ssh_client:
            await callback.message.edit_text(
                "❌ SSH client not available\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_tools")
            )
            return
        
        # Execute update
        success, output = await ssh_client.update_system()
        
        # Format result
        if success:
            text = "✅ *System Update Complete*\n\n"
            text += "System packages have been updated successfully\\.\n\n"
            
            # Check if reboot is required
            if "reboot" in output.lower() or "restart" in output.lower():
                text += "⚠️ _A system reboot may be required\\._"
        else:
            text = "❌ *System Update Failed*\n\n"
            
            # Show error (truncated)
            error_lines = output.strip().split('\n')[-5:]
            text += "```\n"
            for line in error_lines:
                text += f"{escape_markdown(line[:80])}\n"
            text += "```"
        
        # Log action
        if db:
            await db.log_command(
                callback.from_user.id,
                callback.from_user.username,
                "tools_update"
            )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_tools")
        )
        
    except Exception as e:
        logger.error(f"Error executing system update: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to update system: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_tools")
        )
