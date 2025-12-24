"""Handler modules for the Proxmox Telegram Bot."""

from .common import router as common_router
from .vms import router as vms_router

__all__ = ["common_router", "vms_router"]
