"""Text formatting utilities for MarkdownV2."""

import re
from typing import Union


def escape_markdown(text: Union[str, int, float]) -> str:
    """Escape special characters for MarkdownV2 format.
    
    Args:
        text: Text to escape (can be string, int, or float).
        
    Returns:
        str: Escaped text safe for MarkdownV2.
    """
    if text is None:
        return "N/A"
    
    text = str(text)
    
    # Characters that need to be escaped in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Escape each special character
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def format_bytes(bytes_value: Union[int, float], decimals: int = 2) -> str:
    """Format bytes to human-readable format.
    
    Args:
        bytes_value: Number of bytes.
        decimals: Number of decimal places.
        
    Returns:
        str: Formatted string (e.g., "1.5 GB").
    """
    if bytes_value == 0:
        return "0 B"
    
    if bytes_value < 0:
        return "N/A"
    
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    size = float(bytes_value)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.{decimals}f} {units[unit_index]}"


def format_uptime(seconds: int) -> str:
    """Format uptime in seconds to human-readable format.
    
    Args:
        seconds: Uptime in seconds.
        
    Returns:
        str: Formatted uptime (e.g., "2d 5h 30m").
    """
    if seconds < 0:
        return "N/A"
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    if not parts:
        return "< 1m"
    
    return " ".join(parts)
