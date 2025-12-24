"""
VM management handlers.
"""
import logging
from typing import Optional, List, Dict, Any
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from src.services.proxmox import ProxmoxClient
from src.database.db import Database
from src.keyboards.inline import (
    get_vm_list_keyboard,
    get_vm_actions_keyboard,
    get_back_keyboard
)
from src.utils.formatters import escape_markdown, format_vm_info
from src.utils.progress_bars import create_progress_bar, format_bytes, format_uptime

logger = logging.getLogger(__name__)

router = Router()

# Global instances (will be set in main.py)
pve_client: Optional[ProxmoxClient] = None
db: Optional[Database] = None


def set_services(proxmox: ProxmoxClient, database: Database) -> None:
    """Set global service instances."""
    global pve_client, db
    pve_client = proxmox
    db = database


@router.callback_query(F.data == "menu_vms")
async def menu_vms(callback: CallbackQuery) -> None:
    """
    Handle VMs menu callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Loading VMs...")
    
    try:
        # Get VMs from Proxmox
        vms = await pve_client.get_vms()
        
        if not vms:
            await callback.message.edit_text(
                "❌ *No VMs Found*\n\n"
                "No virtual machines or containers found on the Proxmox node\\.",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("main_menu")
            )
            return
        
        # Get user favorites
        favorites = []
        if db:
            fav_list = await db.get_favorites(callback.from_user.id)
            favorites = [fav['vmid'] for fav in fav_list]
        
        # Sort VMs: running first, then by ID
        vms.sort(key=lambda x: (x.get('status') != 'running', x.get('vmid')))
        
        text = (
            f"🖥 *Virtual Machines*\n\n"
            f"Total VMs: {len(vms)}\n"
            f"Running: {sum(1 for vm in vms if vm.get('status') == 'running')}\n"
            f"Stopped: {sum(1 for vm in vms if vm.get('status') == 'stopped')}\n\n"
            f"Select a VM to view details:"
        )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_vm_list_keyboard(vms, page=0, favorites=favorites)
        )
        
    except Exception as e:
        logger.error(f"Error loading VMs: {e}")
        await callback.message.edit_text(
            f"❌ *Error*\n\n"
            f"Failed to load VMs: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("main_menu")
        )


@router.callback_query(F.data.startswith("vm_list_"))
async def vm_list_page(callback: CallbackQuery) -> None:
    """
    Handle VM list pagination.
    
    Args:
        callback: Callback query object
    """
    page = int(callback.data.split("_")[-1])
    
    try:
        # Get VMs from Proxmox
        vms = await pve_client.get_vms()
        
        # Get user favorites
        favorites = []
        if db:
            fav_list = await db.get_favorites(callback.from_user.id)
            favorites = [fav['vmid'] for fav in fav_list]
        
        # Sort VMs
        vms.sort(key=lambda x: (x.get('status') != 'running', x.get('vmid')))
        
        text = (
            f"🖥 *Virtual Machines*\n\n"
            f"Total VMs: {len(vms)}\n"
            f"Running: {sum(1 for vm in vms if vm.get('status') == 'running')}\n"
            f"Stopped: {sum(1 for vm in vms if vm.get('status') == 'stopped')}\n\n"
            f"Select a VM to view details:"
        )
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_vm_list_keyboard(vms, page=page, favorites=favorites)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error loading VMs: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm_info_"))
async def vm_info(callback: CallbackQuery) -> None:
    """
    Handle VM info callback.
    
    Args:
        callback: Callback query object
    """
    vmid = int(callback.data.split("_")[-1])
    await callback.answer("Loading VM info...")
    
    try:
        # Get all VMs to find the target
        vms = await pve_client.get_vms()
        vm = next((v for v in vms if v.get('vmid') == vmid), None)
        
        if not vm:
            await callback.answer("VM not found", show_alert=True)
            return
        
        node = vm.get('node', 'pve')
        vm_type = vm.get('type', 'qemu')
        
        # Get detailed status
        status = await pve_client.get_vm_status(node, vmid, vm_type)
        
        if status:
            vm.update(status)
        
        # Check if favorite
        is_favorite = False
        if db:
            is_favorite = await db.is_favorite(callback.from_user.id, vmid)
        
        # Format VM info
        text = f"🖥 *VM Information*\n\n"
        text += format_vm_info(vm)
        
        # Add node info
        text += f"\nNode: {escape_markdown(node)}\n"
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_vm_actions_keyboard(vmid, vm.get('status', 'unknown'), is_favorite, node)
        )
        
    except Exception as e:
        logger.error(f"Error loading VM info: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm_start_"))
async def vm_start(callback: CallbackQuery) -> None:
    """
    Handle VM start callback.
    
    Args:
        callback: Callback query object
    """
    vmid = int(callback.data.split("_")[-1])
    await callback.answer("Starting VM...")
    
    try:
        # Get VM to find node and type
        vms = await pve_client.get_vms()
        vm = next((v for v in vms if v.get('vmid') == vmid), None)
        
        if not vm:
            await callback.answer("VM not found", show_alert=True)
            return
        
        node = vm.get('node', 'pve')
        vm_type = vm.get('type', 'qemu')
        
        # Start VM
        success = await pve_client.start_vm(node, vmid, vm_type)
        
        if success:
            # Log action
            if db:
                await db.log_command(
                    callback.from_user.id,
                    callback.from_user.username,
                    f"start_vm_{vmid}"
                )
            
            await callback.answer("✅ VM started successfully", show_alert=True)
            
            # Refresh info
            await vm_info(callback)
        else:
            await callback.answer("❌ Failed to start VM", show_alert=True)
        
    except Exception as e:
        logger.error(f"Error starting VM: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm_stop_"))
async def vm_stop(callback: CallbackQuery) -> None:
    """
    Handle VM stop callback.
    
    Args:
        callback: Callback query object
    """
    vmid = int(callback.data.split("_")[-1])
    await callback.answer("Stopping VM...")
    
    try:
        # Get VM to find node and type
        vms = await pve_client.get_vms()
        vm = next((v for v in vms if v.get('vmid') == vmid), None)
        
        if not vm:
            await callback.answer("VM not found", show_alert=True)
            return
        
        node = vm.get('node', 'pve')
        vm_type = vm.get('type', 'qemu')
        
        # Stop VM
        success = await pve_client.stop_vm(node, vmid, vm_type)
        
        if success:
            # Log action
            if db:
                await db.log_command(
                    callback.from_user.id,
                    callback.from_user.username,
                    f"stop_vm_{vmid}"
                )
            
            await callback.answer("✅ VM stopped successfully", show_alert=True)
            
            # Refresh info
            await vm_info(callback)
        else:
            await callback.answer("❌ Failed to stop VM", show_alert=True)
        
    except Exception as e:
        logger.error(f"Error stopping VM: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm_shutdown_"))
async def vm_shutdown(callback: CallbackQuery) -> None:
    """
    Handle VM shutdown callback.
    
    Args:
        callback: Callback query object
    """
    vmid = int(callback.data.split("_")[-1])
    await callback.answer("Shutting down VM...")
    
    try:
        # Get VM to find node and type
        vms = await pve_client.get_vms()
        vm = next((v for v in vms if v.get('vmid') == vmid), None)
        
        if not vm:
            await callback.answer("VM not found", show_alert=True)
            return
        
        node = vm.get('node', 'pve')
        vm_type = vm.get('type', 'qemu')
        
        # Shutdown VM
        success = await pve_client.shutdown_vm(node, vmid, vm_type)
        
        if success:
            # Log action
            if db:
                await db.log_command(
                    callback.from_user.id,
                    callback.from_user.username,
                    f"shutdown_vm_{vmid}"
                )
            
            await callback.answer("✅ VM shutdown initiated", show_alert=True)
            
            # Refresh info
            await vm_info(callback)
        else:
            await callback.answer("❌ Failed to shutdown VM", show_alert=True)
        
    except Exception as e:
        logger.error(f"Error shutting down VM: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm_reboot_"))
async def vm_reboot(callback: CallbackQuery) -> None:
    """
    Handle VM reboot callback.
    
    Args:
        callback: Callback query object
    """
    vmid = int(callback.data.split("_")[-1])
    await callback.answer("Rebooting VM...")
    
    try:
        # Get VM to find node and type
        vms = await pve_client.get_vms()
        vm = next((v for v in vms if v.get('vmid') == vmid), None)
        
        if not vm:
            await callback.answer("VM not found", show_alert=True)
            return
        
        node = vm.get('node', 'pve')
        vm_type = vm.get('type', 'qemu')
        
        # Reboot VM
        success = await pve_client.reboot_vm(node, vmid, vm_type)
        
        if success:
            # Log action
            if db:
                await db.log_command(
                    callback.from_user.id,
                    callback.from_user.username,
                    f"reboot_vm_{vmid}"
                )
            
            await callback.answer("✅ VM reboot initiated", show_alert=True)
            
            # Refresh info
            await vm_info(callback)
        else:
            await callback.answer("❌ Failed to reboot VM", show_alert=True)
        
    except Exception as e:
        logger.error(f"Error rebooting VM: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm_fav_add_"))
async def vm_favorite_add(callback: CallbackQuery) -> None:
    """
    Handle add to favorites callback.
    
    Args:
        callback: Callback query object
    """
    vmid = int(callback.data.split("_")[-1])
    
    try:
        # Get VM info
        vms = await pve_client.get_vms()
        vm = next((v for v in vms if v.get('vmid') == vmid), None)
        
        if not vm:
            await callback.answer("VM not found", show_alert=True)
            return
        
        # Add to favorites
        if db:
            added = await db.add_favorite(
                callback.from_user.id,
                vmid,
                vm.get('name', 'Unknown'),
                vm.get('node', 'pve'),
                vm.get('type', 'qemu')
            )
            
            if added:
                await callback.answer("⭐ Added to favorites", show_alert=True)
            else:
                await callback.answer("Already in favorites", show_alert=True)
            
            # Refresh info
            await vm_info(callback)
        
    except Exception as e:
        logger.error(f"Error adding favorite: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm_fav_remove_"))
async def vm_favorite_remove(callback: CallbackQuery) -> None:
    """
    Handle remove from favorites callback.
    
    Args:
        callback: Callback query object
    """
    vmid = int(callback.data.split("_")[-1])
    
    try:
        # Remove from favorites
        if db:
            removed = await db.remove_favorite(callback.from_user.id, vmid)
            
            if removed:
                await callback.answer("💔 Removed from favorites", show_alert=True)
            else:
                await callback.answer("Not in favorites", show_alert=True)
            
            # Refresh info
            await vm_info(callback)
        
    except Exception as e:
        logger.error(f"Error removing favorite: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm_console_"))
async def vm_console(callback: CallbackQuery) -> None:
    """
    Handle VM console (NoVNC) callback.
    
    Args:
        callback: Callback query object
    """
    vmid = int(callback.data.split("_")[-1])
    
    try:
        # Get VM to find node
        vms = await pve_client.get_vms()
        vm = next((v for v in vms if v.get('vmid') == vmid), None)
        
        if not vm:
            await callback.answer("VM not found", show_alert=True)
            return
        
        node = vm.get('node', 'pve')
        vm_type = vm.get('type', 'qemu')
        
        # Only QEMU VMs support NoVNC
        if vm_type != 'qemu':
            await callback.answer("NoVNC is only available for QEMU VMs", show_alert=True)
            return
        
        # Get VNC ticket
        ticket_data = await pve_client.get_vnc_ticket(node, vmid)
        
        if ticket_data:
            ticket = ticket_data.get('ticket', '')
            port = ticket_data.get('port', '')
            
            # Build NoVNC URL
            novnc_url = f"https://{pve_client.host}:8006/?console=kvm&novnc=1&vmid={vmid}&vmname={vm.get('name')}&node={node}&resize=off&cmd="
            
            text = (
                f"🖥 *NoVNC Console*\n\n"
                f"VM: {escape_markdown(vm.get('name', 'Unknown'))} \\(ID: {vmid}\\)\n"
                f"Node: {escape_markdown(node)}\n\n"
                f"[Open NoVNC Console]({novnc_url})\n\n"
                f"_Note: You may need to accept the SSL certificate\\._"
            )
            
            await callback.message.answer(
                text,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True
            )
            await callback.answer()
        else:
            await callback.answer("Failed to get VNC ticket", show_alert=True)
        
    except Exception as e:
        logger.error(f"Error getting console: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


@router.callback_query(F.data == "vm_favorites")
async def vm_favorites_list(callback: CallbackQuery) -> None:
    """
    Handle favorites list callback.
    
    Args:
        callback: Callback query object
    """
    try:
        if not db:
            await callback.answer("Database not available", show_alert=True)
            return
        
        favorites = await db.get_favorites(callback.from_user.id)
        
        if not favorites:
            await callback.message.edit_text(
                "⭐ *Favorites*\n\n"
                "You haven't added any VMs to favorites yet\\.\n\n"
                "Add VMs to favorites for quick access\\!",
                parse_mode="MarkdownV2",
                reply_markup=get_back_keyboard("menu_vms")
            )
            return
        
        # Get current VM statuses
        vms = await pve_client.get_vms()
        vm_dict = {vm.get('vmid'): vm for vm in vms}
        
        text = f"⭐ *Favorites* \\({len(favorites)}\\)\n\n"
        
        for fav in favorites:
            vmid = fav['vmid']
            name = fav['name']
            vm = vm_dict.get(vmid)
            
            if vm:
                status = vm.get('status', 'unknown')
                status_emoji = '🟢' if status == 'running' else '🔴'
                text += f"{status_emoji} {escape_markdown(name)} \\(ID: {vmid}\\)\n"
            else:
                text += f"⚪️ {escape_markdown(name)} \\(ID: {vmid}\\) \\- _Not found_\n"
        
        # Create keyboard with favorite VMs
        fav_ids = [f['vmid'] for f in favorites]
        fav_vms = [vm for vm in vms if vm.get('vmid') in fav_ids]
        
        await callback.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_vm_list_keyboard(fav_vms, page=0, favorites=fav_ids)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error loading favorites: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


@router.callback_query(F.data == "vm_search")
async def vm_search(callback: CallbackQuery) -> None:
    """
    Handle VM search callback.
    
    Args:
        callback: Callback query object
    """
    await callback.answer("Search feature coming soon!", show_alert=True)
