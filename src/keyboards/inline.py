"""Inline keyboard factories for the bot."""

from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main menu keyboard.
    
    Returns:
        InlineKeyboardMarkup: Main menu keyboard.
    """
    keyboard = [
        [InlineKeyboardButton(text="🖥️ Virtual Machines", callback_data="menu:vms")],
        [InlineKeyboardButton(text="📊 Monitoring", callback_data="menu:monitoring")],
        [InlineKeyboardButton(text="💾 Storage", callback_data="menu:storage")],
        [InlineKeyboardButton(text="⚡ Finance", callback_data="menu:finance")],
        [InlineKeyboardButton(text="📜 Logs", callback_data="menu:logs")],
        [InlineKeyboardButton(text="🔧 Tools", callback_data="menu:tools")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_vm_list_keyboard(vms: List[Dict[str, Any]], show_favorites: bool = False) -> InlineKeyboardMarkup:
    """Create VM list keyboard.
    
    Args:
        vms: List of VM dictionaries with vmid, name, status.
        show_favorites: Whether this is a favorites list.
        
    Returns:
        InlineKeyboardMarkup: VM list keyboard.
    """
    keyboard = []
    
    for vm in vms:
        vmid = vm.get("vmid")
        name = vm.get("name", f"VM {vmid}")
        status = vm.get("status", "unknown")
        
        # Status emoji
        status_emoji = "🟢" if status == "running" else "🔴"
        
        button_text = f"{status_emoji} {name} (ID: {vmid})"
        callback_data = f"vm:info:{vmid}"
        
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    # Navigation buttons
    nav_buttons = []
    if show_favorites:
        nav_buttons.append(InlineKeyboardButton(text="📋 All VMs", callback_data="vm:list:all"))
    else:
        nav_buttons.append(InlineKeyboardButton(text="⭐ Favorites", callback_data="vm:list:favorites"))
    
    nav_buttons.append(InlineKeyboardButton(text="🔍 Search", callback_data="vm:search"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu:main")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_vm_actions_keyboard(vmid: int, status: str, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """Create VM actions keyboard.
    
    Args:
        vmid: VM ID.
        status: VM status (running, stopped).
        is_favorite: Whether VM is in favorites.
        
    Returns:
        InlineKeyboardMarkup: VM actions keyboard.
    """
    keyboard = []
    
    # Action buttons based on status
    if status == "running":
        keyboard.append([
            InlineKeyboardButton(text="⏸️ Stop", callback_data=f"vm:stop:{vmid}"),
            InlineKeyboardButton(text="🔄 Reboot", callback_data=f"vm:reboot:{vmid}")
        ])
        keyboard.append([
            InlineKeyboardButton(text="🛑 Shutdown", callback_data=f"vm:shutdown:{vmid}")
        ])
        keyboard.append([
            InlineKeyboardButton(text="🖥️ NoVNC Console", callback_data=f"vm:novnc:{vmid}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(text="▶️ Start", callback_data=f"vm:start:{vmid}")
        ])
    
    # Favorite button
    if is_favorite:
        keyboard.append([
            InlineKeyboardButton(text="⭐ Remove from Favorites", callback_data=f"vm:unfavorite:{vmid}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(text="⭐ Add to Favorites", callback_data=f"vm:favorite:{vmid}")
        ])
    
    # Navigation
    keyboard.append([
        InlineKeyboardButton(text="🔄 Refresh", callback_data=f"vm:info:{vmid}"),
        InlineKeyboardButton(text="🔙 Back", callback_data="vm:list:all")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_button(callback_data: str = "menu:main", text: str = "🔙 Back") -> InlineKeyboardMarkup:
    """Create a simple back button.
    
    Args:
        callback_data: Callback data for the button.
        text: Button text.
        
    Returns:
        InlineKeyboardMarkup: Back button keyboard.
    """
    keyboard = [[InlineKeyboardButton(text=text, callback_data=callback_data)]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_keyboard(action: str, vmid: int) -> InlineKeyboardMarkup:
    """Create confirmation keyboard.
    
    Args:
        action: Action to confirm (e.g., 'stop', 'reboot').
        vmid: VM ID.
        
    Returns:
        InlineKeyboardMarkup: Confirmation keyboard.
    """
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Yes", callback_data=f"vm:confirm:{action}:{vmid}"),
            InlineKeyboardButton(text="❌ No", callback_data=f"vm:info:{vmid}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_storage_keyboard() -> InlineKeyboardMarkup:
    """Create storage menu keyboard.
    
    Returns:
        InlineKeyboardMarkup: Storage menu keyboard.
    """
    keyboard = [
        [InlineKeyboardButton(text="💿 ISO Images", callback_data="storage:iso:list")],
        [InlineKeyboardButton(text="⬇️ Download ISO", callback_data="storage:iso:download")],
        [InlineKeyboardButton(text="💾 Storages", callback_data="storage:list")],
        [InlineKeyboardButton(text="📦 Backups", callback_data="storage:backups")],
        [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_monitoring_keyboard() -> InlineKeyboardMarkup:
    """Create monitoring menu keyboard.
    
    Returns:
        InlineKeyboardMarkup: Monitoring menu keyboard.
    """
    keyboard = [
        [InlineKeyboardButton(text="💻 Node Status", callback_data="monitor:node")],
        [InlineKeyboardButton(text="🌡️ CPU Temperature", callback_data="monitor:temp")],
        [InlineKeyboardButton(text="💾 Disk SMART", callback_data="monitor:smart")],
        [InlineKeyboardButton(text="🌐 Network", callback_data="monitor:network")],
        [InlineKeyboardButton(text="📊 Load Average", callback_data="monitor:load")],
        [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_logs_keyboard() -> InlineKeyboardMarkup:
    """Create logs menu keyboard.
    
    Returns:
        InlineKeyboardMarkup: Logs menu keyboard.
    """
    keyboard = [
        [InlineKeyboardButton(text="📋 System Logs", callback_data="logs:system")],
        [InlineKeyboardButton(text="📄 Proxmox Logs", callback_data="logs:proxmox")],
        [InlineKeyboardButton(text="🖥️ QEMU Logs", callback_data="logs:qemu")],
        [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_tools_keyboard() -> InlineKeyboardMarkup:
    """Create tools menu keyboard.
    
    Returns:
        InlineKeyboardMarkup: Tools menu keyboard.
    """
    keyboard = [
        [InlineKeyboardButton(text="🏓 Ping", callback_data="tools:ping")],
        [InlineKeyboardButton(text="🛣️ Traceroute", callback_data="tools:traceroute")],
        [InlineKeyboardButton(text="🔄 System Update", callback_data="tools:update")],
        [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
