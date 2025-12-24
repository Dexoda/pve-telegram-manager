"""Progress bars and formatting utilities."""
from typing import Union


def progress_bar(percent: float, length: int = 10) -> str:
    """
    Create a progress bar.
    
    Args:
        percent: Percentage value (0-100)
        length: Length of the progress bar
        
    Returns:
        Progress bar string
    """
    if percent > 100:
        percent = 100
    if percent < 0:
        percent = 0
    
    filled = int(length * percent / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percent:.1f}%"


def format_bytes(bytes_value: Union[int, float]) -> str:
    """
    Format bytes to human-readable format.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_uptime(seconds: int) -> str:
    """
    Format uptime in seconds to human-readable format.
    
    Args:
        seconds: Uptime in seconds
        
    Returns:
        Formatted string (e.g., "5d 3h 25m")
    """
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
    
    return " ".join(parts) if parts else "0m"


def create_progress_bar(
    current: Union[int, float],
    total: Union[int, float],
    length: int = 10,
    filled_char: str = "█",
    empty_char: str = "░"
) -> str:
    """
    Create a text-based progress bar.
    
    Args:
        current: Current value
        total: Total value
        length: Length of the progress bar
        filled_char: Character for filled portion
        empty_char: Character for empty portion
        
    Returns:
        Progress bar string
    """
    if total == 0:
        percentage = 0
    else:
        percentage = (current / total) * 100
    
    filled_length = int(length * current / total) if total > 0 else 0
    bar = filled_char * filled_length + empty_char * (length - filled_length)
    
    return f"{bar} {percentage:.1f}%"


def format_percentage(current: Union[int, float], total: Union[int, float]) -> str:
    """
    Format percentage from current and total values.
    
    Args:
        current: Current value
        total: Total value
        
    Returns:
        Formatted percentage string
    """
    if total == 0:
        return "0.0%"
    percentage = (current / total) * 100
    return f"{percentage:.1f}%"


def format_load_average(load_avg: list) -> str:
    """
    Format load average values.
    
    Args:
        load_avg: List of load average values [1min, 5min, 15min]
        
    Returns:
        Formatted string
    """
    if not load_avg or len(load_avg) < 3:
        return "N/A"
    return f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
