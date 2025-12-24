"""
Progress bars and data formatting utilities.
"""
from typing import Union


def create_progress_bar(
    current: Union[int, float],
    maximum: Union[int, float],
    length: int = 10,
    filled_char: str = "█",
    empty_char: str = "░"
) -> str:
    """
    Create a text-based progress bar.
    
    Args:
        current: Current value
        maximum: Maximum value
        length: Length of progress bar
        filled_char: Character for filled portion
        empty_char: Character for empty portion
        
    Returns:
        Progress bar string
    """
    if maximum <= 0:
        return empty_char * length
    
    percent = min(current / maximum, 1.0)
    filled = int(percent * length)
    empty = length - filled
    
    return filled_char * filled + empty_char * empty


def format_bytes(bytes_value: Union[int, float], decimals: int = 2) -> str:
    """
    Format bytes into human-readable format.
    
    Args:
        bytes_value: Number of bytes
        decimals: Number of decimal places
        
    Returns:
        Formatted string (e.g., "1.23 GB")
    """
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    
    bytes_value = abs(bytes_value)
    unit_index = 0
    
    while bytes_value >= 1024 and unit_index < len(units) - 1:
        bytes_value /= 1024
        unit_index += 1
    
    return f"{bytes_value:.{decimals}f} {units[unit_index]}"


def format_uptime(seconds: int) -> str:
    """
    Format uptime in seconds to human-readable format.
    
    Args:
        seconds: Uptime in seconds
        
    Returns:
        Formatted uptime string (e.g., "2d 5h 30m")
    """
    if seconds < 0:
        return "0m"
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or not parts:
        parts.append(f"{minutes}m")
    
    return " ".join(parts)


def format_percentage(value: Union[int, float], decimals: int = 1) -> str:
    """
    Format a value as percentage.
    
    Args:
        value: Value to format (0-100)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"
