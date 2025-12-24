"""
Storage management handlers.
"""
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.services.proxmox import ProxmoxClient
from src.services.ssh_client import SSHClient
from src.database.db import Database
from src.keyboards.inline import get_storage_list_keyboard, get_back_keyboard
from src.utils.formatters import escape_markdown
from src.utils.progress_bars import format_bytes, create_progress_bar

logger = logging.getLogger(__name__)

router = Router()

# Global instances (will be set in main.py)
pve_client: Optional[ProxmoxClient] = None
ssh_client: Optional[SSHClient] = None
db: Optional[Database] = None


def set_services(proxmox: ProxmoxClient, ssh: SSHClient, database: Database) -> None:
    """Set global service instances."""
    global pve_client, ssh_client, db
    pve_client = proxmox
    ssh_client = ssh
    db = database


@router.callback_query(F.data == "menu_storage")
async def menu_storage(callback: CallbackQuery) -> None:
    """
    Handle storage menu callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Loading storage...")
    
    try:
        # Get storages
        storages = await pve_client.get_storage_list()
        
        if not storages:
            await callback.message.edit_text(
                "❌ *No Storage Found*\n\n"
                "No storage devices found on the Proxmox node\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("main_menu")
            )
            return
        
        text = (
            f"💾 *Storage Management*\n\n"
            f"Total storages: {len(storages)}\n\n"
            f"Select a storage to view details:"
        )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_storage_list_keyboard(storages)
        )
        
    except Exception as e:
        logger.error(f"Error loading storage: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to load storage: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("main_menu")
        )


@router.callback_query(F.data.startswith("storage_info_"))
async def storage_info(callback: CallbackQuery) -> None:
    """
    Handle storage info callback.
    
    Args:
        callback: Callback query object
    """
    storage_id = callback.data.split("_", 2)[-1]
    await callback.answer("Loading storage info...")
    
    try:
        # Get storage list
        storages = await pve_client.get_storage_list()
        storage = next((s for s in storages if s.get('storage') == storage_id), None)
        
        if not storage:
            await callback.answer("Storage not found", show_alert=True)
            return
        
        # Format storage info
        text = f"💾 *Storage Information*\n\n"
        text += f"*Name:* {escape_markdown(storage_id)}\n"
        text += f"*Type:* {escape_markdown(storage.get('type', 'unknown'))}\n"
        text += f"*Status:* {storage.get('status', 'unknown')}\n\n"
        
        # Storage usage
        if 'used' in storage and 'total' in storage:
            used = storage['used']
            total = storage['total']
            percent = (used / total * 100) if total > 0 else 0
            
            bar = create_progress_bar(percent, 100)
            text += f"*Usage:*\n"
            text += f"{escape_markdown(format_bytes(used))} / {escape_markdown(format_bytes(total))}\n"
            text += f"`{bar}` {percent:.1f}%\n\n"
        
        # Content types
        if 'content' in storage:
            content = storage['content']
            text += f"*Content Types:*\n{escape_markdown(content)}\n"
        
        # Log action
        if db:
            await db.log_command(
                callback.from_user.id,
                callback.from_user.username,
                f"storage_info_{storage_id}"
            )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_storage")
        )
        
    except Exception as e:
        logger.error(f"Error loading storage info: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


@router.callback_query(F.data == "storage_iso_list")
async def storage_iso_list(callback: CallbackQuery) -> None:
    """
    Handle ISO list callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Loading ISO images...")
    
    try:
        # Get all storages
        storages = await pve_client.get_storage_list()
        
        # Find storages that support ISO
        iso_storages = [s for s in storages if 'iso' in s.get('content', '').lower()]
        
        if not iso_storages:
            await callback.message.edit_text(
                "❌ *No ISO Storage*\n\n"
                "No storage with ISO content type found\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_storage")
            )
            return
        
        # Get ISO content from all ISO storages
        all_isos = []
        for storage in iso_storages:
            storage_id = storage.get('storage')
            try:
                isos = await pve_client.get_storage_content(
                    node="pve",
                    storage=storage_id,
                    content_type="iso"
                )
                for iso in isos:
                    iso['storage'] = storage_id
                all_isos.extend(isos)
            except Exception as e:
                logger.warning(f"Error getting ISOs from {storage_id}: {e}")
        
        if not all_isos:
            text = (
                "📀 *ISO Images*\n\n"
                "No ISO images found\\.\n\n"
                "_You can download ISO images using the download feature\\._"
            )
        else:
            text = f"📀 *ISO Images* \\({len(all_isos)}\\)\n\n"
            
            for iso in all_isos[:20]:  # Limit to 20 ISOs
                volid = iso.get('volid', '')
                size = iso.get('size', 0)
                storage = iso.get('storage', 'unknown')
                
                # Extract filename from volid
                filename = volid.split('/')[-1] if '/' in volid else volid
                
                text += f"📀 {escape_markdown(filename)}\n"
                text += f"   Size: {escape_markdown(format_bytes(size))}\n"
                text += f"   Storage: {escape_markdown(storage)}\n\n"
            
            if len(all_isos) > 20:
                text += f"_\\.\\.\\. and {len(all_isos) - 20} more_\n"
        
        # Log action
        if db:
            await db.log_command(
                callback.from_user.id,
                callback.from_user.username,
                "storage_iso_list"
            )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_storage")
        )
        
    except Exception as e:
        logger.error(f"Error loading ISO list: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to load ISO images: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_storage")
        )


@router.callback_query(F.data == "storage_backups")
async def storage_backups(callback: CallbackQuery) -> None:
    """
    Handle backups list callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Loading backups...")
    
    try:
        # Get all storages
        storages = await pve_client.get_storage_list()
        
        # Find storages that support backups
        backup_storages = [s for s in storages if 'backup' in s.get('content', '').lower() or s.get('type') == 'dir']
        
        if not backup_storages:
            await callback.message.edit_text(
                "❌ *No Backup Storage*\n\n"
                "No storage with backup content type found\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_storage")
            )
            return
        
        # Get backup content from all backup storages
        all_backups = []
        for storage in backup_storages:
            storage_id = storage.get('storage')
            try:
                backups = await pve_client.get_storage_content(
                    node="pve",
                    storage=storage_id,
                    content_type="backup"
                )
                for backup in backups:
                    backup['storage'] = storage_id
                all_backups.extend(backups)
            except Exception as e:
                logger.warning(f"Error getting backups from {storage_id}: {e}")
        
        if not all_backups:
            text = (
                "💿 *Backups*\n\n"
                "No backups found\\."
            )
        else:
            text = f"💿 *Backups* \\({len(all_backups)}\\)\n\n"
            
            # Sort by creation time (if available)
            all_backups.sort(key=lambda x: x.get('ctime', 0), reverse=True)
            
            for backup in all_backups[:15]:  # Limit to 15 backups
                volid = backup.get('volid', '')
                size = backup.get('size', 0)
                storage = backup.get('storage', 'unknown')
                
                # Extract filename from volid
                filename = volid.split('/')[-1] if '/' in volid else volid
                
                text += f"💿 {escape_markdown(filename)}\n"
                text += f"   Size: {escape_markdown(format_bytes(size))}\n"
                text += f"   Storage: {escape_markdown(storage)}\n\n"
            
            if len(all_backups) > 15:
                text += f"_\\.\\.\\. and {len(all_backups) - 15} more_\n"
        
        # Log action
        if db:
            await db.log_command(
                callback.from_user.id,
                callback.from_user.username,
                "storage_backups"
            )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_storage")
        )
        
    except Exception as e:
        logger.error(f"Error loading backups: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to load backups: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("menu_storage")
        )
