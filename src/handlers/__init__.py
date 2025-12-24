"""Handler modules for the Proxmox Telegram Bot."""

from .common import router as common_router
from .vms import router as vms_router
from .monitoring import router as monitoring_router
from .storage import router as storage_router

__all__ = ["common_router", "vms_router", "monitoring_router", "storage_router"]
