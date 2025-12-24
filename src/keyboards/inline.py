"""Inline keyboards for Telegram bot."""
from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu() -> InlineKeyboardMarkup:
    """
    Create main menu keyboard.
    
    Returns:
        InlineKeyboardMarkup with main menu buttons
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🖥️ Virtual Machines", callback_data="menu_vms")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Monitoring", callback_data="menu_monitoring"),
        InlineKeyboardButton(text="💾 Storage", callback_data="menu_storage")
    )
    builder.row(
        InlineKeyboardButton(text="🛠️ Tools", callback_data="menu_tools"),
        InlineKeyboardButton(text="📝 Logs", callback_data="menu_logs")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Finance", callback_data="menu_finance")
    )
    
    return builder.as_markup()


def get_status_emoji(status: str) -> str:
    """
    Get emoji for VM status.
    
    Args:
        status: VM status
        
    Returns:
        Status emoji
    """
    status_emojis = {
        "running": "🟢",
        "stopped": "🔴",
        "paused": "🟡",
        "suspended": "🟠",
    }
    return status_emojis.get(status.lower(), "⚪")


def vm_list_keyboard(vms: List[Dict[str, Any]], page: int = 0, page_size: int = 10) -> InlineKeyboardMarkup:
    """
    Create keyboard with list of VMs.
    
    Args:
        vms: List of VMs
        page: Current page number
        page_size: Number of VMs per page
        
    Returns:
        InlineKeyboardMarkup with VM list
    """
    builder = InlineKeyboardBuilder()
    
    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_vms = vms[start_idx:end_idx]
    
    for vm in page_vms:
        vmid = vm.get("vmid")
        name = vm.get("name", f"VM {vmid}")
        status = vm.get("status", "unknown")
        node = vm.get("node", "")
        vm_type = vm.get("type", "qemu")
        
        emoji = get_status_emoji(status)
        button_text = f"{emoji} {name} ({vmid})"
        
        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"vm_info:{node}:{vmid}:{vm_type}"
            )
        )
    
    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Previous", callback_data=f"vm_list:page:{page-1}")
        )
    if end_idx < len(vms):
        nav_buttons.append(
            InlineKeyboardButton(text="Next ➡️", callback_data=f"vm_list:page:{page+1}")
        )
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Back button
    builder.row(
        InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu_main")
    )
    
    return builder.as_markup()


def vm_actions_keyboard(
    vmid: int,
    node: str,
    status: str,
    vm_type: str,
    is_favorite: bool = False
) -> InlineKeyboardMarkup:
    """
    Create keyboard with VM actions.
    
    Args:
        vmid: VM ID
        node: Node name
        status: Current VM status
        vm_type: VM type (qemu or lxc)
        is_favorite: Whether VM is in favorites
        
    Returns:
        InlineKeyboardMarkup with VM actions
    """
    builder = InlineKeyboardBuilder()
    
    # Action buttons based on status
    if status.lower() == "running":
        builder.row(
            InlineKeyboardButton(
                text="🔄 Reboot",
                callback_data=f"vm_reboot:{node}:{vmid}:{vm_type}"
            ),
            InlineKeyboardButton(
                text="⏹️ Shutdown",
                callback_data=f"vm_shutdown:{node}:{vmid}:{vm_type}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🛑 Stop (Force)",
                callback_data=f"vm_stop:{node}:{vmid}:{vm_type}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🖥️ NoVNC Console",
                callback_data=f"vm_novnc:{node}:{vmid}:{vm_type}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="▶️ Start",
                callback_data=f"vm_start:{node}:{vmid}:{vm_type}"
            )
        )
    
    # Favorite button
    if is_favorite:
        builder.row(
            InlineKeyboardButton(
                text="⭐ Remove from Favorites",
                callback_data=f"vm_unfavorite:{node}:{vmid}:{vm_type}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="☆ Add to Favorites",
                callback_data=f"vm_favorite:{node}:{vmid}:{vm_type}"
            )
        )
    
    # Refresh and back buttons
    builder.row(
        InlineKeyboardButton(
            text="🔄 Refresh",
            callback_data=f"vm_info:{node}:{vmid}:{vm_type}"
        ),
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="menu_vms"
        )
    )
    
    return builder.as_markup()


def monitoring_menu() -> InlineKeyboardMarkup:
    """
    Create monitoring menu keyboard.
    
    Returns:
        InlineKeyboardMarkup with monitoring options
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="💻 CPU & RAM", callback_data="mon_cpu_ram")
    )
    builder.row(
        InlineKeyboardButton(text="🌡️ Temperature", callback_data="mon_temperature"),
        InlineKeyboardButton(text="📊 Load Average", callback_data="mon_load")
    )
    builder.row(
        InlineKeyboardButton(text="💾 SMART Status", callback_data="mon_smart"),
        InlineKeyboardButton(text="💿 Disk Usage", callback_data="mon_disks")
    )
    builder.row(
        InlineKeyboardButton(text="📶 Network Stats", callback_data="mon_network")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu_main")
    )
    
    return builder.as_markup()


def storage_menu() -> InlineKeyboardMarkup:
    """
    Create storage menu keyboard.
    
    Returns:
        InlineKeyboardMarkup with storage options
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📦 Storage List", callback_data="storage_list")
    )
    builder.row(
        InlineKeyboardButton(text="💿 ISO Images", callback_data="storage_iso"),
        InlineKeyboardButton(text="💾 Backups", callback_data="storage_backups")
    )
    builder.row(
        InlineKeyboardButton(text="📥 Download ISO", callback_data="storage_download_iso")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu_main")
    )
    
    return builder.as_markup()


def tools_menu() -> InlineKeyboardMarkup:
    """
    Create tools menu keyboard.
    
    Returns:
        InlineKeyboardMarkup with tools options
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔍 Ping Host", callback_data="tools_ping")
    )
    builder.row(
        InlineKeyboardButton(text="🛣️ Traceroute", callback_data="tools_traceroute")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Update System", callback_data="tools_update")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu_main")
    )
    
    return builder.as_markup()


def logs_menu() -> InlineKeyboardMarkup:
    """
    Create logs menu keyboard.
    
    Returns:
        InlineKeyboardMarkup with logs options
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📋 System Logs", callback_data="logs_system")
    )
    builder.row(
        InlineKeyboardButton(text="🖥️ Proxmox Logs", callback_data="logs_proxmox"),
        InlineKeyboardButton(text="🔧 QEMU Logs", callback_data="logs_qemu")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Bot Command Logs", callback_data="logs_commands")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu_main")
    )
    
    return builder.as_markup()


def confirm_keyboard(action: str, callback_data: str) -> InlineKeyboardMarkup:
    """
    Create confirmation keyboard.
    
    Args:
        action: Action description
        callback_data: Callback data for confirmation
        
    Returns:
        InlineKeyboardMarkup with confirmation buttons
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Confirm", callback_data=f"confirm:{callback_data}"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")
    )
    
    return builder.as_markup()


def back_button(callback_data: str = "menu_main") -> InlineKeyboardMarkup:
    """
    Create simple back button keyboard.
    
    Args:
        callback_data: Callback data for back button
        
    Returns:
        InlineKeyboardMarkup with back button
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data=callback_data)
    )
    return builder.as_markup()
