"""Keyboards package initialization."""
from .inline import (
    get_main_menu_keyboard,
    get_vm_list_keyboard,
    get_vm_actions_keyboard,
    get_back_keyboard,
    get_confirmation_keyboard,
    get_storage_list_keyboard,
    get_monitoring_menu_keyboard
)

__all__ = [
    'get_main_menu_keyboard',
    'get_vm_list_keyboard',
    'get_vm_actions_keyboard',
    'get_back_keyboard',
    'get_confirmation_keyboard',
    'get_storage_list_keyboard',
    'get_monitoring_menu_keyboard'
]
