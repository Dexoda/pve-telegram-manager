"""VM management handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramAPIError
import logging

from src.keyboards.inline import (
    vm_list_keyboard,
    vm_actions_keyboard,
    main_menu,
    back_button
)
from src.utils.formatters import escape_markdown_v2, format_bold
from src.utils.progress_bars import format_bytes, format_uptime, create_progress_bar

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("vms"))
@router.callback_query(F.data == "menu_vms")
async def show_vms(event, proxmox, db) -> None:
    """
    Show list of all VMs.
    
    Args:
        event: Message or CallbackQuery
        proxmox: Proxmox client
        db: Database instance
    """
    try:
        # Determine event type
        is_callback = isinstance(event, CallbackQuery)
        user = event.from_user
        
        # Log command
        await db.log_command(
            user_id=user.id,
            username=user.username,
            command="/vms" if not is_callback else "menu_vms"
        )
        
        # Send "loading" message
        if is_callback:
            await event.answer("Loading VMs...")
        else:
            loading_msg = await event.answer("⏳ Loading VMs...")
        
        # Get all VMs
        vms = await proxmox.get_all_vms()
        
        if not vms:
            text = "No virtual machines found\\."
            if is_callback:
                await event.message.edit_text(text, parse_mode="MarkdownV2")
            else:
                await loading_msg.edit_text(text, parse_mode="MarkdownV2")
            return
        
        # Sort VMs by node and vmid
        vms.sort(key=lambda x: (x.get('node', ''), x.get('vmid', 0)))
        
        text = f"🖥️ *Virtual Machines* \\({len(vms)} total\\)\n\nSelect a VM to manage:"
        keyboard = vm_list_keyboard(vms)
        
        if is_callback:
            await event.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="MarkdownV2"
            )
        else:
            await loading_msg.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="MarkdownV2"
            )
        
    except Exception as e:
        logger.error(f"Error showing VMs: {e}", exc_info=True)
        error_msg = "An error occurred while loading VMs\\."
        
        if is_callback:
            await event.answer("Error loading VMs", show_alert=True)
        else:
            await event.answer(error_msg, parse_mode="MarkdownV2")


@router.message(Command("favorites"))
async def show_favorites(message: Message, proxmox, db) -> None:
    """
    Show favorite VMs.
    
    Args:
        message: Message object
        proxmox: Proxmox client
        db: Database instance
    """
    try:
        user = message.from_user
        
        # Log command
        await db.log_command(
            user_id=user.id,
            username=user.username,
            command="/favorites"
        )
        
        # Get favorites
        favorites = await db.get_favorites(user.id)
        
        if not favorites:
            await message.answer(
                "⭐ You don't have any favorite VMs yet\\.\n\n"
                "Add VMs to favorites from the VM info page\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        # Get current status for favorites
        vms = []
        for fav in favorites:
            try:
                status = await proxmox.get_vm_status(
                    fav['node'],
                    fav['vmid'],
                    fav['vm_type']
                )
                vms.append({
                    'vmid': fav['vmid'],
                    'node': fav['node'],
                    'name': fav['name'] or f"VM {fav['vmid']}",
                    'status': status.get('status', 'unknown'),
                    'type': fav['vm_type']
                })
            except Exception as e:
                logger.error(f"Error getting status for favorite VM {fav['vmid']}: {e}")
        
        text = f"⭐ *Favorite VMs* \\({len(vms)} total\\)\n\nSelect a VM to manage:"
        keyboard = vm_list_keyboard(vms)
        
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing favorites: {e}", exc_info=True)
        await message.answer("An error occurred while loading favorites\\.", parse_mode="MarkdownV2")


@router.callback_query(F.data.startswith("vm_info:"))
async def show_vm_info(callback: CallbackQuery, proxmox, db) -> None:
    """
    Show VM information.
    
    Args:
        callback: CallbackQuery object
        proxmox: Proxmox client
        db: Database instance
    """
    try:
        # Parse callback data: vm_info:node:vmid:vm_type
        parts = callback.data.split(":")
        node = parts[1]
        vmid = int(parts[2])
        vm_type = parts[3]
        
        await callback.answer("Loading VM info...")
        
        # Get VM status and config
        status = await proxmox.get_vm_status(node, vmid, vm_type)
        config = await proxmox.get_vm_config(node, vmid, vm_type)
        
        # Check if favorite
        is_favorite = await db.is_favorite(callback.from_user.id, vmid, node)
        
        # Format VM info
        name = config.get('name', f'VM {vmid}')
        vm_status = status.get('status', 'unknown')
        
        text = f"🖥️ *VM Information*\n\n"
        text += f"*Name:* {escape_markdown_v2(name)}\n"
        text += f"*VMID:* `{vmid}`\n"
        text += f"*Node:* {escape_markdown_v2(node)}\n"
        text += f"*Type:* {escape_markdown_v2(vm_type.upper())}\n"
        text += f"*Status:* {escape_markdown_v2(vm_status.upper())}\n\n"
        
        # Add resource information if running
        if vm_status == "running":
            text += "*Resources:*\n"
            
            # CPU
            if 'cpu' in status:
                cpu_usage = status['cpu'] * 100
                text += f"CPU: {cpu_usage:.1f}%\n"
            
            # Memory
            if 'mem' in status and 'maxmem' in status:
                mem_used = format_bytes(status['mem'])
                mem_total = format_bytes(status['maxmem'])
                mem_percent = (status['mem'] / status['maxmem'] * 100) if status['maxmem'] > 0 else 0
                text += f"RAM: {escape_markdown_v2(mem_used)} / {escape_markdown_v2(mem_total)} \\({mem_percent:.1f}%\\)\n"
            
            # Disk
            if 'disk' in status and 'maxdisk' in status:
                disk_used = format_bytes(status['disk'])
                disk_total = format_bytes(status['maxdisk'])
                disk_percent = (status['disk'] / status['maxdisk'] * 100) if status['maxdisk'] > 0 else 0
                text += f"Disk: {escape_markdown_v2(disk_used)} / {escape_markdown_v2(disk_total)} \\({disk_percent:.1f}%\\)\n"
            
            # Uptime
            if 'uptime' in status:
                uptime_str = format_uptime(status['uptime'])
                text += f"Uptime: {escape_markdown_v2(uptime_str)}\n"
        
        # Add config info
        text += "\n*Configuration:*\n"
        
        if 'cores' in config:
            text += f"Cores: {config['cores']}\n"
        
        if 'memory' in config:
            mem = format_bytes(config['memory'] * 1024 * 1024)
            text += f"Memory: {escape_markdown_v2(mem)}\n"
        
        if 'net0' in config:
            text += f"Network: {escape_markdown_v2(str(config['net0']))}\n"
        
        # Create keyboard
        keyboard = vm_actions_keyboard(vmid, node, vm_status, vm_type, is_favorite)
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing VM info: {e}", exc_info=True)
        await callback.answer("Error loading VM info", show_alert=True)


@router.callback_query(F.data.startswith("vm_start:"))
async def start_vm(callback: CallbackQuery, proxmox, db) -> None:
    """Start VM."""
    try:
        parts = callback.data.split(":")
        node = parts[1]
        vmid = int(parts[2])
        vm_type = parts[3]
        
        await callback.answer("Starting VM...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="vm_start",
            parameters=f"{node}:{vmid}:{vm_type}"
        )
        
        # Start VM
        await proxmox.start_vm(node, vmid, vm_type)
        
        await callback.answer("✅ VM start initiated", show_alert=True)
        
        # Refresh info
        await show_vm_info(callback, proxmox, db)
        
    except Exception as e:
        logger.error(f"Error starting VM: {e}", exc_info=True)
        await callback.answer("❌ Error starting VM", show_alert=True)


@router.callback_query(F.data.startswith("vm_stop:"))
async def stop_vm(callback: CallbackQuery, proxmox, db) -> None:
    """Stop VM (force)."""
    try:
        parts = callback.data.split(":")
        node = parts[1]
        vmid = int(parts[2])
        vm_type = parts[3]
        
        await callback.answer("Stopping VM...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="vm_stop",
            parameters=f"{node}:{vmid}:{vm_type}"
        )
        
        # Stop VM
        await proxmox.stop_vm(node, vmid, vm_type)
        
        await callback.answer("✅ VM stop initiated", show_alert=True)
        
        # Refresh info
        await show_vm_info(callback, proxmox, db)
        
    except Exception as e:
        logger.error(f"Error stopping VM: {e}", exc_info=True)
        await callback.answer("❌ Error stopping VM", show_alert=True)


@router.callback_query(F.data.startswith("vm_shutdown:"))
async def shutdown_vm(callback: CallbackQuery, proxmox, db) -> None:
    """Shutdown VM gracefully."""
    try:
        parts = callback.data.split(":")
        node = parts[1]
        vmid = int(parts[2])
        vm_type = parts[3]
        
        await callback.answer("Shutting down VM...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="vm_shutdown",
            parameters=f"{node}:{vmid}:{vm_type}"
        )
        
        # Shutdown VM
        await proxmox.shutdown_vm(node, vmid, vm_type)
        
        await callback.answer("✅ VM shutdown initiated", show_alert=True)
        
        # Refresh info
        await show_vm_info(callback, proxmox, db)
        
    except Exception as e:
        logger.error(f"Error shutting down VM: {e}", exc_info=True)
        await callback.answer("❌ Error shutting down VM", show_alert=True)


@router.callback_query(F.data.startswith("vm_reboot:"))
async def reboot_vm(callback: CallbackQuery, proxmox, db) -> None:
    """Reboot VM."""
    try:
        parts = callback.data.split(":")
        node = parts[1]
        vmid = int(parts[2])
        vm_type = parts[3]
        
        await callback.answer("Rebooting VM...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="vm_reboot",
            parameters=f"{node}:{vmid}:{vm_type}"
        )
        
        # Reboot VM
        await proxmox.reboot_vm(node, vmid, vm_type)
        
        await callback.answer("✅ VM reboot initiated", show_alert=True)
        
        # Refresh info
        await show_vm_info(callback, proxmox, db)
        
    except Exception as e:
        logger.error(f"Error rebooting VM: {e}", exc_info=True)
        await callback.answer("❌ Error rebooting VM", show_alert=True)


@router.callback_query(F.data.startswith("vm_favorite:"))
async def add_favorite(callback: CallbackQuery, proxmox, db) -> None:
    """Add VM to favorites."""
    try:
        parts = callback.data.split(":")
        node = parts[1]
        vmid = int(parts[2])
        vm_type = parts[3]
        
        # Get VM name
        config = await proxmox.get_vm_config(node, vmid, vm_type)
        name = config.get('name', f'VM {vmid}')
        
        # Add to favorites
        added = await db.add_favorite(
            user_id=callback.from_user.id,
            vmid=vmid,
            node=node,
            vm_type=vm_type,
            name=name
        )
        
        if added:
            await callback.answer("⭐ Added to favorites", show_alert=True)
        else:
            await callback.answer("Already in favorites", show_alert=True)
        
        # Refresh info
        await show_vm_info(callback, proxmox, db)
        
    except Exception as e:
        logger.error(f"Error adding favorite: {e}", exc_info=True)
        await callback.answer("❌ Error adding favorite", show_alert=True)


@router.callback_query(F.data.startswith("vm_unfavorite:"))
async def remove_favorite(callback: CallbackQuery, db, proxmox) -> None:
    """Remove VM from favorites."""
    try:
        parts = callback.data.split(":")
        node = parts[1]
        vmid = int(parts[2])
        vm_type = parts[3]
        
        # Remove from favorites
        removed = await db.remove_favorite(
            user_id=callback.from_user.id,
            vmid=vmid,
            node=node
        )
        
        if removed:
            await callback.answer("Removed from favorites", show_alert=True)
        else:
            await callback.answer("Not in favorites", show_alert=True)
        
        # Refresh info
        await show_vm_info(callback, proxmox, db)
        
    except Exception as e:
        logger.error(f"Error removing favorite: {e}", exc_info=True)
        await callback.answer("❌ Error removing favorite", show_alert=True)


@router.callback_query(F.data.startswith("vm_novnc:"))
async def show_novnc(callback: CallbackQuery, proxmox, config) -> None:
    """Show NoVNC console link."""
    try:
        parts = callback.data.split(":")
        node = parts[1]
        vmid = int(parts[2])
        
        # Get VNC ticket
        ticket_data = await proxmox.get_vnc_ticket(node, vmid)
        
        # Build NoVNC URL
        port = ticket_data.get('port')
        ticket = ticket_data.get('ticket')
        
        novnc_url = (
            f"https://{config.PVE_HOST}:{config.PVE_PORT}/"
            f"?console=kvm&novnc=1&vmid={vmid}&vmname=VM{vmid}"
            f"&node={node}&resize=scale&cmd="
        )
        
        text = (
            f"🖥️ *NoVNC Console*\n\n"
            f"*VM:* {vmid}\n"
            f"*Node:* {escape_markdown_v2(node)}\n\n"
            f"[Open Console]({novnc_url})\n\n"
            f"_Note: You need to be logged in to Proxmox web interface\\._"
        )
        
        await callback.message.answer(
            text,
            parse_mode="MarkdownV2",
            reply_markup=back_button("menu_vms")
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing NoVNC: {e}", exc_info=True)
        await callback.answer("❌ Error getting console access", show_alert=True)
