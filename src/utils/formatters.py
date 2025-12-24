"""
Formatters module for MarkdownV2 escaping and text formatting.
"""
import re
from typing import Dict, Any


def escape_markdown(text: str) -> str:
    """
    Escape special characters for MarkdownV2 format.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for MarkdownV2
    """
    if not text:
        return ""
    
    # Characters that need to be escaped in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Escape each special character
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def format_vm_status(status: str) -> str:
    """
    Format VM status with emoji.
    
    Args:
        status: VM status (running, stopped, etc.)
        
    Returns:
        Formatted status with emoji
    """
    status_map = {
        'running': '🟢 Running',
        'stopped': '🔴 Stopped',
        'paused': '🟡 Paused',
    }
    return status_map.get(status.lower(), f'⚪️ {status.capitalize()}')


def format_vm_info(vm: Dict[str, Any]) -> str:
    """
    Format VM information for display.
    
    Args:
        vm: VM data dictionary
        
    Returns:
        Formatted VM information
    """
    vmid = vm.get('vmid', 'N/A')
    name = escape_markdown(vm.get('name', 'Unknown'))
    status = format_vm_status(vm.get('status', 'unknown'))
    vm_type = vm.get('type', 'qemu').upper()
    
    info = f"*{name}* \\(ID: {vmid}\\)\n"
    info += f"Type: {vm_type}\n"
    info += f"Status: {status}\n"
    
    # Add CPU and memory if available
    if 'cpu' in vm:
        cpu_percent = vm.get('cpu', 0) * 100
        info += f"CPU: {cpu_percent:.1f}%\n"
    
    if 'mem' in vm and 'maxmem' in vm:
        mem_mb = vm.get('mem', 0) / (1024 * 1024)
        maxmem_mb = vm.get('maxmem', 1) / (1024 * 1024)
        mem_percent = (vm.get('mem', 0) / vm.get('maxmem', 1)) * 100 if vm.get('maxmem', 0) > 0 else 0
        info += f"Memory: {mem_mb:.0f}/{maxmem_mb:.0f} MB \\({mem_percent:.1f}%\\)\n"
    
    # Add uptime if running
    if vm.get('status') == 'running' and 'uptime' in vm:
        from .progress_bars import format_uptime
        uptime = format_uptime(vm.get('uptime', 0))
        info += f"Uptime: {escape_markdown(uptime)}\n"
    
    return info
