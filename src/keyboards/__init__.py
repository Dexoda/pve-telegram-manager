"""Keyboard modules for the Proxmox Telegram Bot."""

from .inline import *

__all__ = [
    "get_main_menu_keyboard",
    "get_vm_list_keyboard",
    "get_vm_actions_keyboard",
    "get_back_button",
    "get_confirmation_keyboard",
    "get_storage_keyboard",
    "get_monitoring_keyboard",
    "get_logs_keyboard",
    "get_tools_keyboard",
]
