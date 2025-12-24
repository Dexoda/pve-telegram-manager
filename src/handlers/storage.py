"""Storage management handlers."""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.config import Config
from src.database import Database
from src.services.proxmox import ProxmoxClient
from src.services.ssh_client import SSHClient
from src.keyboards.inline import get_storage_keyboard, get_back_button
from src.utils.formatters import escape_markdown, format_bytes
from src.utils.progress_bars import create_percentage_bar

logger = logging.getLogger(__name__)

router = Router()

# Global state for dependency injection
_config: Config = None
_db: Database = None
_proxmox: ProxmoxClient = None
_ssh: SSHClient = None


class ISODownloadStates(StatesGroup):
    """States for ISO download flow."""
    waiting_for_url = State()


def setup_storage_router(config: Config, db: Database, proxmox: ProxmoxClient, ssh: SSHClient):
    """Setup storage router with dependencies.
    
    Args:
        config: Application configuration.
        db: Database instance.
        proxmox: Proxmox client instance.
        ssh: SSH client instance.
    """
    global _config, _db, _proxmox, _ssh
    _config = config
    _db = db
    _proxmox = proxmox
    _ssh = ssh


@router.callback_query(F.data == "menu:storage")
async def callback_storage_menu(callback: CallbackQuery):
    """Handle storage menu callback.
    
    Args:
        callback: Callback query.
    """
    await _db.log_command(callback.from_user.id, callback.from_user.username, "storage:menu")
    
    await callback.message.edit_text(
        "💾 *Storage Management*\n\n"
        "Select storage option:",
        reply_markup=get_storage_keyboard(),
        parse_mode="MarkdownV2"
    )
    await callback.answer()


@router.callback_query(F.data == "storage:iso:list")
async def callback_storage_iso_list(callback: CallbackQuery):
    """Handle ISO list callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading ISO images...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "storage:iso:list")
    
    try:
        # Get all nodes
        nodes = await _proxmox.get_nodes()
        
        if not nodes:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "No nodes found\\.",
                reply_markup=get_back_button("menu:storage"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Get ISO images from all storages
        all_isos = []
        
        for node in nodes:
            node_name = node.get('node')
            
            try:
                # Get all storages for this node
                storages = await _proxmox.get_storage_list(node_name)
                
                for storage in storages:
                    storage_name = storage.get('storage')
                    
                    # Check if storage supports ISO content
                    content_types = storage.get('content', '').split(',')
                    if 'iso' in content_types:
                        try:
                            # Get ISO content
                            isos = await _proxmox.get_storage_content(node_name, storage_name, 'iso')
                            for iso in isos:
                                iso['node'] = node_name
                                iso['storage'] = storage_name
                                all_isos.append(iso)
                        except Exception as e:
                            logger.warning(f"Failed to get ISOs from {storage_name}: {e}")
            except Exception as e:
                logger.warning(f"Failed to get storages from {node_name}: {e}")
        
        if not all_isos:
            await callback.message.edit_text(
                "💿 *ISO Images*\n\n"
                "No ISO images found\\.",
                reply_markup=get_back_button("menu:storage"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Format ISO list
        messages = [f"💿 *ISO Images* \\({len(all_isos)} total\\)\n"]
        
        for iso in all_isos[:20]:  # Limit to 20 to avoid message length issues
            volid = iso.get('volid', '')
            size = iso.get('size', 0)
            
            # Extract filename from volid
            filename = volid.split('/')[-1] if '/' in volid else volid
            
            messages.append(
                f"📀 {escape_markdown(filename)}\n"
                f"   Size: {escape_markdown(format_bytes(size))}\n"
                f"   Storage: {escape_markdown(iso.get('storage', 'N/A'))}\n"
            )
        
        if len(all_isos) > 20:
            messages.append(f"\n_\\.\\.\\. and {len(all_isos) - 20} more_")
        
        text = "\n".join(messages)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("menu:storage"),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get ISO list: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve ISO list: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:storage"),
            parse_mode="MarkdownV2"
        )


@router.callback_query(F.data == "storage:iso:download")
async def callback_storage_iso_download(callback: CallbackQuery):
    """Handle ISO download callback.
    
    Args:
        callback: Callback query.
    """
    await _db.log_command(callback.from_user.id, callback.from_user.username, "storage:iso:download")
    
    await callback.message.edit_text(
        "⬇️ *Download ISO*\n\n"
        "ISO download feature requires manual URL input\\.\n\n"
        "Use SSH to download ISOs:\n"
        "```\ncd /var/lib/vz/template/iso\nwget <URL>\n```",
        reply_markup=get_back_button("menu:storage"),
        parse_mode="MarkdownV2"
    )
    await callback.answer()


@router.callback_query(F.data == "storage:list")
async def callback_storage_list(callback: CallbackQuery):
    """Handle storage list callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading storages...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "storage:list")
    
    try:
        # Get all nodes
        nodes = await _proxmox.get_nodes()
        
        if not nodes:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "No nodes found\\.",
                reply_markup=get_back_button("menu:storage"),
                parse_mode="MarkdownV2"
            )
            return
        
        messages = ["💾 *Storage Pools*\n"]
        
        for node in nodes:
            node_name = node.get('node')
            
            try:
                # Get node status for storage info
                status = await _proxmox.get_node_status(node_name)
                
                # Root filesystem
                rootfs = status.get('rootfs', {})
                rootfs_used = rootfs.get('used', 0)
                rootfs_total = rootfs.get('total', 1)
                rootfs_percent = (rootfs_used / rootfs_total * 100) if rootfs_total > 0 else 0
                
                messages.append(f"\n📍 *{escape_markdown(node_name)}*")
                messages.append(f"\n*Root Filesystem*")
                messages.append(f"Used: {escape_markdown(format_bytes(rootfs_used))} / {escape_markdown(format_bytes(rootfs_total))}")
                messages.append(create_percentage_bar(rootfs_percent) + f" {rootfs_percent:.1f}%")
                
                # Get storage list
                storages = await _proxmox.get_storage_list(node_name)
                
                for storage in storages:
                    storage_name = storage.get('storage', 'unknown')
                    storage_type = storage.get('type', 'unknown')
                    enabled = storage.get('enabled', 1)
                    active = storage.get('active', 0)
                    
                    if not enabled or not active:
                        continue
                    
                    # Get storage content to check usage
                    used_bytes = storage.get('used', 0)
                    total_bytes = storage.get('total', 1)
                    
                    if total_bytes > 0:
                        used_percent = (used_bytes / total_bytes * 100)
                        
                        messages.append(f"\n*{escape_markdown(storage_name)}* \\({escape_markdown(storage_type)}\\)")
                        messages.append(f"{escape_markdown(format_bytes(used_bytes))} / {escape_markdown(format_bytes(total_bytes))}")
                        messages.append(create_percentage_bar(used_percent) + f" {used_percent:.1f}%")
                
            except Exception as e:
                logger.error(f"Failed to get storage info for {node_name}: {e}")
                messages.append(f"\n📍 *{escape_markdown(node_name)}*")
                messages.append(f"⚠️ Failed to get storage info")
        
        text = "\n".join(messages)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("menu:storage"),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get storage list: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve storage list: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:storage"),
            parse_mode="MarkdownV2"
        )


@router.callback_query(F.data == "storage:backups")
async def callback_storage_backups(callback: CallbackQuery):
    """Handle backups list callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading backups...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "storage:backups")
    
    try:
        # Get all nodes
        nodes = await _proxmox.get_nodes()
        
        if not nodes:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "No nodes found\\.",
                reply_markup=get_back_button("menu:storage"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Get backups from all storages
        all_backups = []
        
        for node in nodes:
            node_name = node.get('node')
            
            try:
                # Get all storages for this node
                storages = await _proxmox.get_storage_list(node_name)
                
                for storage in storages:
                    storage_name = storage.get('storage')
                    
                    # Check if storage supports backup content
                    content_types = storage.get('content', '').split(',')
                    if 'backup' in content_types:
                        try:
                            # Get backup content
                            backups = await _proxmox.get_storage_content(node_name, storage_name, 'backup')
                            for backup in backups:
                                backup['node'] = node_name
                                backup['storage'] = storage_name
                                all_backups.append(backup)
                        except Exception as e:
                            logger.warning(f"Failed to get backups from {storage_name}: {e}")
            except Exception as e:
                logger.warning(f"Failed to get storages from {node_name}: {e}")
        
        if not all_backups:
            await callback.message.edit_text(
                "📦 *Backups*\n\n"
                "No backups found\\.",
                reply_markup=get_back_button("menu:storage"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Sort by date (newest first)
        all_backups.sort(key=lambda x: x.get('ctime', 0), reverse=True)
        
        # Format backup list
        messages = [f"📦 *Backups* \\({len(all_backups)} total\\)\n"]
        
        for backup in all_backups[:15]:  # Limit to 15
            volid = backup.get('volid', '')
            size = backup.get('size', 0)
            
            # Extract filename from volid
            filename = volid.split('/')[-1] if '/' in volid else volid
            
            messages.append(
                f"📦 {escape_markdown(filename)}\n"
                f"   Size: {escape_markdown(format_bytes(size))}\n"
                f"   Storage: {escape_markdown(backup.get('storage', 'N/A'))}\n"
            )
        
        if len(all_backups) > 15:
            messages.append(f"\n_\\.\\.\\. and {len(all_backups) - 15} more_")
        
        text = "\n".join(messages)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("menu:storage"),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get backups: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve backups: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:storage"),
            parse_mode="MarkdownV2"
        )
