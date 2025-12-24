"""Storage management handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
import logging

from src.keyboards.inline import storage_menu, back_button
from src.utils.formatters import escape_markdown_v2, format_pre
from src.utils.progress_bars import format_bytes

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "menu_storage")
async def show_storage_menu(callback: CallbackQuery, db) -> None:
    """Show storage menu."""
    try:
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="menu_storage"
        )
        
        await callback.message.edit_text(
            "💾 *Storage Management*\n\nSelect storage option:",
            reply_markup=storage_menu(),
            parse_mode="MarkdownV2"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing storage menu: {e}")
        await callback.answer("Error", show_alert=True)


@router.callback_query(F.data == "storage_list")
async def show_storage_list(callback: CallbackQuery, proxmox, db) -> None:
    """Show list of storage."""
    try:
        await callback.answer("Loading...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="storage_list"
        )
        
        nodes = await proxmox.get_nodes()
        
        if not nodes:
            await callback.message.edit_text(
                "No nodes found\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        text = "📦 *Storage List*\n\n"
        
        for node_info in nodes:
            node = node_info['node']
            storage_list = await proxmox.get_storage_list(node)
            
            if storage_list:
                text += f"*Node:* {escape_markdown_v2(node)}\n"
                
                for storage in storage_list:
                    storage_name = storage.get('storage', 'unknown')
                    storage_type = storage.get('type', 'unknown')
                    
                    # Get storage status if available
                    if 'total' in storage and 'used' in storage:
                        total = format_bytes(storage['total'])
                        used = format_bytes(storage['used'])
                        avail = format_bytes(storage.get('avail', 0))
                        percent = (storage['used'] / storage['total'] * 100) if storage['total'] > 0 else 0
                        
                        text += f"  • {escape_markdown_v2(storage_name)} \\({escape_markdown_v2(storage_type)}\\)\n"
                        text += f"    Used: {escape_markdown_v2(used)} / {escape_markdown_v2(total)} \\({percent:.1f}%\\)\n"
                        text += f"    Available: {escape_markdown_v2(avail)}\n"
                    else:
                        text += f"  • {escape_markdown_v2(storage_name)} \\({escape_markdown_v2(storage_type)}\\)\n"
                
                text += "\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_storage"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing storage list: {e}", exc_info=True)
        await callback.answer("Error loading storage", show_alert=True)


@router.callback_query(F.data == "storage_iso")
async def show_iso_images(callback: CallbackQuery, proxmox, db) -> None:
    """Show ISO images."""
    try:
        await callback.answer("Loading...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="storage_iso"
        )
        
        nodes = await proxmox.get_nodes()
        
        text = "💿 *ISO Images*\n\n"
        found_iso = False
        
        for node_info in nodes:
            node = node_info['node']
            storage_list = await proxmox.get_storage_list(node)
            
            for storage in storage_list:
                storage_name = storage.get('storage')
                content = await proxmox.get_storage_content(node, storage_name, 'iso')
                
                if content:
                    found_iso = True
                    text += f"*Storage:* {escape_markdown_v2(storage_name)} \\({escape_markdown_v2(node)}\\)\n"
                    
                    for iso in content:
                        volid = iso.get('volid', 'unknown')
                        size = format_bytes(iso.get('size', 0))
                        text += f"  • {escape_markdown_v2(volid.split('/')[-1])} \\({escape_markdown_v2(size)}\\)\n"
                    
                    text += "\n"
        
        if not found_iso:
            text += "No ISO images found\\."
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_storage"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing ISO images: {e}", exc_info=True)
        await callback.answer("Error loading ISOs", show_alert=True)


@router.callback_query(F.data == "storage_backups")
async def show_backups(callback: CallbackQuery, proxmox, db) -> None:
    """Show backups."""
    try:
        await callback.answer("Loading...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="storage_backups"
        )
        
        nodes = await proxmox.get_nodes()
        
        text = "💾 *Backups*\n\n"
        found_backup = False
        
        for node_info in nodes:
            node = node_info['node']
            storage_list = await proxmox.get_storage_list(node)
            
            for storage in storage_list:
                storage_name = storage.get('storage')
                content = await proxmox.get_storage_content(node, storage_name, 'backup')
                
                if content:
                    found_backup = True
                    text += f"*Storage:* {escape_markdown_v2(storage_name)} \\({escape_markdown_v2(node)}\\)\n"
                    
                    for backup in content[:10]:  # Limit to 10 backups per storage
                        volid = backup.get('volid', 'unknown')
                        size = format_bytes(backup.get('size', 0))
                        text += f"  • {escape_markdown_v2(volid.split('/')[-1])} \\({escape_markdown_v2(size)}\\)\n"
                    
                    if len(content) > 10:
                        text += f"  _\\.\\.\\. and {len(content) - 10} more_\n"
                    
                    text += "\n"
        
        if not found_backup:
            text += "No backups found\\."
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_storage"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing backups: {e}", exc_info=True)
        await callback.answer("Error loading backups", show_alert=True)


@router.callback_query(F.data == "storage_download_iso")
async def download_iso_prompt(callback: CallbackQuery, db) -> None:
    """Prompt for ISO download."""
    try:
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="storage_download_iso"
        )
        
        text = (
            "📥 *Download ISO*\n\n"
            "To download an ISO image, you need to provide:\n"
            "1\\. URL of the ISO file\n"
            "2\\. Storage path on Proxmox server\n\n"
            "_This feature requires SSH access\\._\n\n"
            "Please contact the administrator to download ISO images\\."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_storage"),
            parse_mode="MarkdownV2"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing ISO download prompt: {e}")
        await callback.answer("Error", show_alert=True)
