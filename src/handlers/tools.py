"""System tools handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

from src.keyboards.inline import tools_menu, back_button
from src.utils.formatters import format_pre, escape_markdown_v2

logger = logging.getLogger(__name__)

router = Router()


class ToolsStates(StatesGroup):
    """States for tools."""
    waiting_for_ping_host = State()
    waiting_for_traceroute_host = State()


@router.callback_query(F.data == "menu_tools")
async def show_tools_menu(callback: CallbackQuery, db) -> None:
    """Show tools menu."""
    try:
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="menu_tools"
        )
        
        await callback.message.edit_text(
            "🛠️ *System Tools*\n\nSelect a tool:",
            reply_markup=tools_menu(),
            parse_mode="MarkdownV2"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing tools menu: {e}")
        await callback.answer("Error", show_alert=True)


@router.callback_query(F.data == "tools_ping")
async def ping_prompt(callback: CallbackQuery, db) -> None:
    """Prompt for ping host."""
    try:
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="tools_ping"
        )
        
        text = (
            "🔍 *Ping Host*\n\n"
            "This feature allows you to ping a host from the Proxmox server\\.\n\n"
            "_Example usage:_\n"
            "`/ping 8\\.8\\.8\\.8`\n"
            "`/ping google\\.com`\n\n"
            "Send a message with `/ping <host>` to test connectivity\\."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_tools"),
            parse_mode="MarkdownV2"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing ping prompt: {e}")
        await callback.answer("Error", show_alert=True)


@router.callback_query(F.data == "tools_traceroute")
async def traceroute_prompt(callback: CallbackQuery, db) -> None:
    """Prompt for traceroute host."""
    try:
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="tools_traceroute"
        )
        
        text = (
            "🛣️ *Traceroute*\n\n"
            "This feature allows you to trace the route to a host\\.\n\n"
            "_Example usage:_\n"
            "`/traceroute 8\\.8\\.8\\.8`\n"
            "`/traceroute google\\.com`\n\n"
            "Send a message with `/traceroute <host>` to trace the route\\."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_tools"),
            parse_mode="MarkdownV2"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing traceroute prompt: {e}")
        await callback.answer("Error", show_alert=True)


@router.callback_query(F.data == "tools_update")
async def update_system(callback: CallbackQuery, ssh_client, db) -> None:
    """Update system packages."""
    try:
        await callback.answer("Starting system update...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="tools_update"
        )
        
        if not ssh_client:
            await callback.message.edit_text(
                "❌ SSH client not configured\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        # Send progress message
        progress_msg = await callback.message.edit_text(
            "🔄 *System Update*\n\nUpdating system packages\\.\\.\\.\n_This may take a few minutes\\._",
            parse_mode="MarkdownV2"
        )
        
        # Run update
        update_output = await ssh_client.update_system()
        
        text = "🔄 *System Update*\n\n"
        text += format_pre(update_output[:3500])
        
        await progress_msg.edit_text(
            text,
            reply_markup=back_button("menu_tools"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error updating system: {e}", exc_info=True)
        await callback.answer("Error updating system", show_alert=True)


# Message handlers for ping and traceroute commands
@router.message(F.text.startswith("/ping "))
async def cmd_ping(message: Message, ssh_client, db) -> None:
    """Handle /ping command."""
    try:
        user = message.from_user
        
        # Extract host
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("Usage: `/ping <host>`", parse_mode="MarkdownV2")
            return
        
        host = parts[1].strip()
        
        # Log command
        await db.log_command(
            user_id=user.id,
            username=user.username,
            command="/ping",
            parameters=host
        )
        
        if not ssh_client:
            await message.answer("❌ SSH client not configured\\.", parse_mode="MarkdownV2")
            return
        
        # Send progress message
        progress_msg = await message.answer(f"🔍 Pinging {escape_markdown_v2(host)}\\.\\.\\.", parse_mode="MarkdownV2")
        
        # Run ping
        ping_output = await ssh_client.ping_host(host, count=4)
        
        text = f"🔍 *Ping Results*\n\n*Host:* {escape_markdown_v2(host)}\n\n"
        text += format_pre(ping_output[:3500])
        
        await progress_msg.edit_text(text, parse_mode="MarkdownV2")
        
    except Exception as e:
        logger.error(f"Error in ping command: {e}", exc_info=True)
        await message.answer("Error executing ping\\.", parse_mode="MarkdownV2")


@router.message(F.text.startswith("/traceroute "))
async def cmd_traceroute(message: Message, ssh_client, db) -> None:
    """Handle /traceroute command."""
    try:
        user = message.from_user
        
        # Extract host
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("Usage: `/traceroute <host>`", parse_mode="MarkdownV2")
            return
        
        host = parts[1].strip()
        
        # Log command
        await db.log_command(
            user_id=user.id,
            username=user.username,
            command="/traceroute",
            parameters=host
        )
        
        if not ssh_client:
            await message.answer("❌ SSH client not configured\\.", parse_mode="MarkdownV2")
            return
        
        # Send progress message
        progress_msg = await message.answer(
            f"🛣️ Tracing route to {escape_markdown_v2(host)}\\.\\.\\.\n_This may take a minute\\._",
            parse_mode="MarkdownV2"
        )
        
        # Run traceroute
        traceroute_output = await ssh_client.traceroute_host(host)
        
        text = f"🛣️ *Traceroute Results*\n\n*Host:* {escape_markdown_v2(host)}\n\n"
        text += format_pre(traceroute_output[:3500])
        
        await progress_msg.edit_text(text, parse_mode="MarkdownV2")
        
    except Exception as e:
        logger.error(f"Error in traceroute command: {e}", exc_info=True)
        await message.answer("Error executing traceroute\\.", parse_mode="MarkdownV2")
