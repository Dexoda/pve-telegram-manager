"""
Inline keyboard factories for bot navigation.
"""
from typing import List, Dict, Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Get main menu keyboard.
    
    Returns:
        Main menu inline keyboard
    """
    buttons = [
        [InlineKeyboardButton(text="🖥 Virtual Machines", callback_data="menu_vms")],
        [InlineKeyboardButton(text="📊 Monitoring", callback_data="menu_monitoring")],
        [InlineKeyboardButton(text="💾 Storage", callback_data="menu_storage")],
        [InlineKeyboardButton(text="🔧 Tools", callback_data="menu_tools")],
        [InlineKeyboardButton(text="💰 Finance", callback_data="menu_finance")],
        [InlineKeyboardButton(text="📋 Logs", callback_data="menu_logs")],
        [InlineKeyboardButton(text="❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vm_list_keyboard(
    vms: List[Dict[str, Any]],
    page: int = 0,
    per_page: int = 10,
    favorites: Optional[List[int]] = None
) -> InlineKeyboardMarkup:
    """
    Get VM list keyboard with pagination.
    
    Args:
        vms: List of VMs
        page: Current page number
        per_page: VMs per page
        favorites: List of favorite VM IDs
        
    Returns:
        VM list inline keyboard
    """
    favorites = favorites or []
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_vms = vms[start_idx:end_idx]
    
    buttons = []
    
    for vm in page_vms:
        vmid = vm.get('vmid')
        name = vm.get('name', 'Unknown')
        status = vm.get('status', 'unknown')
        
        # Status emoji
        status_emoji = '🟢' if status == 'running' else '🔴'
        
        # Favorite emoji
        fav_emoji = '⭐' if vmid in favorites else ''
        
        button_text = f"{status_emoji} {fav_emoji}{name} (ID: {vmid})"
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"vm_info_{vmid}"
        )])
    
    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"vm_list_{page-1}"))
    if end_idx < len(vms):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"vm_list_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Additional options
    buttons.append([
        InlineKeyboardButton(text="⭐ Favorites", callback_data="vm_favorites"),
        InlineKeyboardButton(text="🔍 Search", callback_data="vm_search")
    ])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vm_actions_keyboard(
    vmid: int,
    status: str,
    is_favorite: bool = False,
    node: str = "pve"
) -> InlineKeyboardMarkup:
    """
    Get VM actions keyboard based on status.
    
    Args:
        vmid: VM ID
        status: VM status
        is_favorite: Whether VM is in favorites
        node: Proxmox node name
        
    Returns:
        VM actions inline keyboard
    """
    buttons = []
    
    # Action buttons based on status
    if status == 'running':
        buttons.append([
            InlineKeyboardButton(text="⏸ Shutdown", callback_data=f"vm_shutdown_{vmid}"),
            InlineKeyboardButton(text="⏹ Stop", callback_data=f"vm_stop_{vmid}")
        ])
        buttons.append([
            InlineKeyboardButton(text="🔄 Reboot", callback_data=f"vm_reboot_{vmid}")
        ])
        buttons.append([
            InlineKeyboardButton(text="🖥 Console (NoVNC)", callback_data=f"vm_console_{vmid}")
        ])
    elif status == 'stopped':
        buttons.append([
            InlineKeyboardButton(text="▶️ Start", callback_data=f"vm_start_{vmid}")
        ])
    
    # Favorite toggle
    fav_text = "💔 Remove from Favorites" if is_favorite else "⭐ Add to Favorites"
    fav_action = "remove" if is_favorite else "add"
    buttons.append([
        InlineKeyboardButton(text=fav_text, callback_data=f"vm_fav_{fav_action}_{vmid}")
    ])
    
    # Refresh and back
    buttons.append([
        InlineKeyboardButton(text="🔄 Refresh", callback_data=f"vm_info_{vmid}"),
        InlineKeyboardButton(text="🔙 Back", callback_data="menu_vms")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """
    Get simple back button keyboard.
    
    Args:
        callback_data: Callback data for back button
        
    Returns:
        Back button inline keyboard
    """
    buttons = [[InlineKeyboardButton(text="🔙 Back", callback_data=callback_data)]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirmation_keyboard(action: str, target_id: str) -> InlineKeyboardMarkup:
    """
    Get confirmation keyboard for destructive actions.
    
    Args:
        action: Action to confirm
        target_id: Target identifier
        
    Returns:
        Confirmation inline keyboard
    """
    buttons = [
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data=f"confirm_{action}_{target_id}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"cancel_{action}_{target_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_storage_list_keyboard(storages: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Get storage list keyboard.
    
    Args:
        storages: List of storages
        
    Returns:
        Storage list inline keyboard
    """
    buttons = []
    
    for storage in storages:
        storage_id = storage.get('storage')
        storage_type = storage.get('type', 'unknown')
        
        button_text = f"💾 {storage_id} ({storage_type})"
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"storage_info_{storage_id}"
        )])
    
    buttons.append([
        InlineKeyboardButton(text="📀 ISO Images", callback_data="storage_iso_list"),
        InlineKeyboardButton(text="💿 Backups", callback_data="storage_backups")
    ])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_monitoring_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Get monitoring menu keyboard.
    
    Returns:
        Monitoring menu inline keyboard
    """
    buttons = [
        [InlineKeyboardButton(text="📊 Node Status", callback_data="mon_node_status")],
        [InlineKeyboardButton(text="🌡 CPU Temperature", callback_data="mon_cpu_temp")],
        [InlineKeyboardButton(text="💽 Disk Status", callback_data="mon_disk_status")],
        [InlineKeyboardButton(text="🔍 SMART Status", callback_data="mon_smart_status")],
        [InlineKeyboardButton(text="🌐 Network Traffic", callback_data="mon_network")],
        [InlineKeyboardButton(text="⚡ Load Average", callback_data="mon_load_avg")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
