"""VM management handlers."""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.config import Config
from src.database import Database
from src.services.proxmox import ProxmoxClient
from src.keyboards.inline import (
    get_vm_list_keyboard,
    get_vm_actions_keyboard,
    get_back_button,
    get_confirmation_keyboard
)
from src.utils.formatters import escape_markdown, format_bytes, format_uptime
from src.utils.progress_bars import create_percentage_bar, get_status_emoji

logger = logging.getLogger(__name__)

router = Router()

# Global state for dependency injection
_config: Config = None
_db: Database = None
_proxmox: ProxmoxClient = None


def setup_vms_router(config: Config, db: Database, proxmox: ProxmoxClient):
    """Setup VMs router with dependencies.
    
    Args:
        config: Application configuration.
        db: Database instance.
        proxmox: Proxmox client instance.
    """
    global _config, _db, _proxmox
    _config = config
    _db = db
    _proxmox = proxmox


@router.callback_query(F.data == "menu:vms")
async def callback_vms_menu(callback: CallbackQuery):
    """Handle VMs menu callback - show VM list.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading VMs...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "vm:list")
    
    try:
        # Get all VMs
        vms = await _proxmox.get_vms()
        
        if not vms:
            await callback.message.edit_text(
                "🖥️ *Virtual Machines*\n\n"
                "No VMs found\\.",
                reply_markup=get_back_button("menu:main"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Sort by status (running first) and then by vmid
        vms_sorted = sorted(vms, key=lambda x: (x.get('status') != 'running', x.get('vmid')))
        
        await callback.message.edit_text(
            f"🖥️ *Virtual Machines* \\({len(vms)} total\\)\n\n"
            "Select a VM to manage:",
            reply_markup=get_vm_list_keyboard(vms_sorted),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get VMs: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve VMs: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:main"),
            parse_mode="MarkdownV2"
        )


@router.callback_query(F.data == "vm:list:all")
async def callback_vm_list_all(callback: CallbackQuery):
    """Handle show all VMs callback.
    
    Args:
        callback: Callback query.
    """
    await callback_vms_menu(callback)


@router.callback_query(F.data == "vm:list:favorites")
async def callback_vm_list_favorites(callback: CallbackQuery):
    """Handle show favorites callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Loading favorites...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, "vm:favorites")
    
    try:
        # Get user's favorites
        favorites = await _db.get_favorites(callback.from_user.id)
        
        if not favorites:
            await callback.message.edit_text(
                "⭐ *Favorite VMs*\n\n"
                "You don't have any favorite VMs yet\\.\n\n"
                "Add VMs to favorites from the VM details page\\.",
                reply_markup=get_back_button("menu:vms"),
                parse_mode="MarkdownV2"
            )
            return
        
        # Get current status for favorites
        all_vms = await _proxmox.get_vms()
        vm_map = {vm['vmid']: vm for vm in all_vms}
        
        favorite_vms = []
        for fav in favorites:
            vm = vm_map.get(fav['vmid'])
            if vm:
                favorite_vms.append(vm)
        
        await callback.message.edit_text(
            f"⭐ *Favorite VMs* \\({len(favorite_vms)} total\\)\n\n"
            "Select a VM to manage:",
            reply_markup=get_vm_list_keyboard(favorite_vms, show_favorites=True),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get favorites: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve favorites: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:vms"),
            parse_mode="MarkdownV2"
        )


@router.callback_query(F.data.startswith("vm:info:"))
async def callback_vm_info(callback: CallbackQuery):
    """Handle VM info callback.
    
    Args:
        callback: Callback query.
    """
    vmid = int(callback.data.split(":")[2])
    await callback.answer("Loading VM info...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, f"vm:info:{vmid}")
    
    try:
        # Find VM in list to get node and type
        vms = await _proxmox.get_vms()
        vm = next((v for v in vms if v['vmid'] == vmid), None)
        
        if not vm:
            await callback.message.edit_text(
                "❌ *Error*\n\n"
                "VM not found\\.",
                reply_markup=get_back_button("menu:vms"),
                parse_mode="MarkdownV2"
            )
            return
        
        node = vm['node']
        vm_type = vm['type']
        
        # Get detailed status
        status = await _proxmox.get_vm_status(node, vmid, vm_type)
        config = await _proxmox.get_vm_config(node, vmid, vm_type)
        
        # Format VM information
        vm_name = vm.get('name', f"VM {vmid}")
        vm_status = status.get('status', 'unknown')
        status_emoji = get_status_emoji(vm_status)
        
        # Build info text
        info_lines = [
            f"{status_emoji} *{escape_markdown(vm_name)}*",
            "",
            f"*ID:* {escape_markdown(vmid)}",
            f"*Type:* {escape_markdown(vm_type.upper())}",
            f"*Node:* {escape_markdown(node)}",
            f"*Status:* {escape_markdown(vm_status.title())}",
            ""
        ]
        
        # CPU and Memory
        if vm_status == 'running':
            cpu_usage = status.get('cpu', 0) * 100
            cpus = status.get('cpus', config.get('cores', 1))
            
            mem_used = status.get('mem', 0)
            mem_max = status.get('maxmem', 1)
            mem_percent = (mem_used / mem_max * 100) if mem_max > 0 else 0
            
            info_lines.append(f"*CPU:* {cpu_usage:.1f}% \\({cpus} cores\\)")
            info_lines.append(create_percentage_bar(cpu_usage) + f" {cpu_usage:.1f}%")
            info_lines.append("")
            info_lines.append(f"*Memory:* {escape_markdown(format_bytes(mem_used))} / {escape_markdown(format_bytes(mem_max))}")
            info_lines.append(create_percentage_bar(mem_percent) + f" {mem_percent:.1f}%")
            info_lines.append("")
            
            # Uptime
            uptime = status.get('uptime', 0)
            if uptime > 0:
                info_lines.append(f"*Uptime:* {escape_markdown(format_uptime(uptime))}")
                info_lines.append("")
        
        # Disk info
        if vm_type == 'qemu':
            disk_size = config.get('bootdisk', 'N/A')
            info_lines.append(f"*Boot Disk:* {escape_markdown(disk_size)}")
        
        # Check if in favorites
        is_favorite = await _db.is_favorite(callback.from_user.id, vmid)
        
        info_text = "\n".join(info_lines)
        
        await callback.message.edit_text(
            info_text,
            reply_markup=get_vm_actions_keyboard(vmid, vm_status, is_favorite),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to get VM info: {e}")
        await callback.message.edit_text(
            "❌ *Error*\n\n"
            f"Failed to retrieve VM info: {escape_markdown(str(e))}",
            reply_markup=get_back_button("menu:vms"),
            parse_mode="MarkdownV2"
        )


@router.callback_query(F.data.startswith("vm:start:"))
async def callback_vm_start(callback: CallbackQuery):
    """Handle VM start callback.
    
    Args:
        callback: Callback query.
    """
    vmid = int(callback.data.split(":")[2])
    await callback.answer("Starting VM...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, f"vm:start:{vmid}")
    
    try:
        # Find VM to get node and type
        vms = await _proxmox.get_vms()
        vm = next((v for v in vms if v['vmid'] == vmid), None)
        
        if not vm:
            await callback.answer("VM not found", show_alert=True)
            return
        
        # Start VM
        await _proxmox.start_vm(vm['node'], vmid, vm['type'])
        
        await callback.answer("✅ VM start command sent")
        
        # Refresh VM info
        await callback_vm_info(callback)
    except Exception as e:
        logger.error(f"Failed to start VM: {e}")
        await callback.answer(f"❌ Failed to start VM: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm:stop:"))
async def callback_vm_stop(callback: CallbackQuery):
    """Handle VM stop callback.
    
    Args:
        callback: Callback query.
    """
    vmid = int(callback.data.split(":")[2])
    await callback.answer("Stopping VM...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, f"vm:stop:{vmid}")
    
    try:
        # Find VM to get node and type
        vms = await _proxmox.get_vms()
        vm = next((v for v in vms if v['vmid'] == vmid), None)
        
        if not vm:
            await callback.answer("VM not found", show_alert=True)
            return
        
        # Stop VM
        await _proxmox.stop_vm(vm['node'], vmid, vm['type'])
        
        await callback.answer("✅ VM stop command sent")
        
        # Refresh VM info
        await callback_vm_info(callback)
    except Exception as e:
        logger.error(f"Failed to stop VM: {e}")
        await callback.answer(f"❌ Failed to stop VM: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm:shutdown:"))
async def callback_vm_shutdown(callback: CallbackQuery):
    """Handle VM shutdown callback.
    
    Args:
        callback: Callback query.
    """
    vmid = int(callback.data.split(":")[2])
    await callback.answer("Shutting down VM...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, f"vm:shutdown:{vmid}")
    
    try:
        # Find VM to get node and type
        vms = await _proxmox.get_vms()
        vm = next((v for v in vms if v['vmid'] == vmid), None)
        
        if not vm:
            await callback.answer("VM not found", show_alert=True)
            return
        
        # Shutdown VM
        await _proxmox.shutdown_vm(vm['node'], vmid, vm['type'])
        
        await callback.answer("✅ VM shutdown command sent")
        
        # Refresh VM info
        await callback_vm_info(callback)
    except Exception as e:
        logger.error(f"Failed to shutdown VM: {e}")
        await callback.answer(f"❌ Failed to shutdown VM: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm:reboot:"))
async def callback_vm_reboot(callback: CallbackQuery):
    """Handle VM reboot callback.
    
    Args:
        callback: Callback query.
    """
    vmid = int(callback.data.split(":")[2])
    await callback.answer("Rebooting VM...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, f"vm:reboot:{vmid}")
    
    try:
        # Find VM to get node and type
        vms = await _proxmox.get_vms()
        vm = next((v for v in vms if v['vmid'] == vmid), None)
        
        if not vm:
            await callback.answer("VM not found", show_alert=True)
            return
        
        # Reboot VM
        await _proxmox.reboot_vm(vm['node'], vmid, vm['type'])
        
        await callback.answer("✅ VM reboot command sent")
        
        # Refresh VM info
        await callback_vm_info(callback)
    except Exception as e:
        logger.error(f"Failed to reboot VM: {e}")
        await callback.answer(f"❌ Failed to reboot VM: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm:favorite:"))
async def callback_vm_favorite(callback: CallbackQuery):
    """Handle add to favorites callback.
    
    Args:
        callback: Callback query.
    """
    vmid = int(callback.data.split(":")[2])
    await _db.log_command(callback.from_user.id, callback.from_user.username, f"vm:favorite:{vmid}")
    
    try:
        # Find VM to get details
        vms = await _proxmox.get_vms()
        vm = next((v for v in vms if v['vmid'] == vmid), None)
        
        if not vm:
            await callback.answer("VM not found", show_alert=True)
            return
        
        # Add to favorites
        added = await _db.add_favorite(
            callback.from_user.id,
            vmid,
            vm.get('name', f"VM {vmid}"),
            vm['node'],
            vm['type']
        )
        
        if added:
            await callback.answer("⭐ Added to favorites")
        else:
            await callback.answer("Already in favorites")
        
        # Refresh VM info
        await callback_vm_info(callback)
    except Exception as e:
        logger.error(f"Failed to add favorite: {e}")
        await callback.answer(f"❌ Failed to add favorite: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm:unfavorite:"))
async def callback_vm_unfavorite(callback: CallbackQuery):
    """Handle remove from favorites callback.
    
    Args:
        callback: Callback query.
    """
    vmid = int(callback.data.split(":")[2])
    await _db.log_command(callback.from_user.id, callback.from_user.username, f"vm:unfavorite:{vmid}")
    
    try:
        # Remove from favorites
        removed = await _db.remove_favorite(callback.from_user.id, vmid)
        
        if removed:
            await callback.answer("⭐ Removed from favorites")
        else:
            await callback.answer("Not in favorites")
        
        # Refresh VM info
        await callback_vm_info(callback)
    except Exception as e:
        logger.error(f"Failed to remove favorite: {e}")
        await callback.answer(f"❌ Failed to remove favorite: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("vm:novnc:"))
async def callback_vm_novnc(callback: CallbackQuery):
    """Handle NoVNC console callback.
    
    Args:
        callback: Callback query.
    """
    vmid = int(callback.data.split(":")[2])
    await callback.answer("Generating console link...")
    await _db.log_command(callback.from_user.id, callback.from_user.username, f"vm:novnc:{vmid}")
    
    try:
        # Find VM to get node
        vms = await _proxmox.get_vms()
        vm = next((v for v in vms if v['vmid'] == vmid), None)
        
        if not vm or vm['type'] != 'qemu':
            await callback.answer("NoVNC only available for QEMU VMs", show_alert=True)
            return
        
        # Get VNC ticket
        ticket_data = await _proxmox.get_vnc_ticket(vm['node'], vmid)
        
        # Build NoVNC URL
        port = ticket_data.get('port')
        ticket = ticket_data.get('ticket')
        
        novnc_url = (
            f"https://{_config.proxmox.host}:8006/"
            f"?console=kvm&novnc=1&vmid={vmid}&vmname={vm.get('name', '')}"
            f"&node={vm['node']}&resize=scale&port={port}"
        )
        
        await callback.message.answer(
            f"🖥️ *NoVNC Console*\n\n"
            f"VM: {escape_markdown(vm.get('name', f'VM {vmid}'))}\n"
            f"Node: {escape_markdown(vm['node'])}\n\n"
            f"[Open Console]({novnc_url})\n\n"
            f"_Note: You may need to accept the security certificate\\._",
            parse_mode="MarkdownV2",
            disable_web_page_preview=True
        )
        
        await callback.answer("✅ Console link generated")
    except Exception as e:
        logger.error(f"Failed to generate NoVNC link: {e}")
        await callback.answer(f"❌ Failed to generate console link: {str(e)}", show_alert=True)


@router.callback_query(F.data == "vm:search")
async def callback_vm_search(callback: CallbackQuery):
    """Handle VM search callback.
    
    Args:
        callback: Callback query.
    """
    await callback.answer("Search feature coming soon!")
