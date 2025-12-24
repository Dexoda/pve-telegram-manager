"""Progress bar utilities for resource visualization."""

from typing import Union


def create_progress_bar(
    current: Union[int, float],
    total: Union[int, float],
    length: int = 10,
    fill_char: str = "█",
    empty_char: str = "░"
) -> str:
    """Create a text-based progress bar.
    
    Args:
        current: Current value.
        total: Maximum value.
        length: Length of the progress bar in characters.
        fill_char: Character for filled portion.
        empty_char: Character for empty portion.
        
    Returns:
        str: Progress bar string.
    """
    if total <= 0:
        return empty_char * length
    
    percentage = min(100, max(0, (current / total) * 100))
    filled = int((percentage / 100) * length)
    empty = length - filled
    
    return fill_char * filled + empty_char * empty


def create_percentage_bar(
    percentage: Union[int, float],
    length: int = 10,
    fill_char: str = "█",
    empty_char: str = "░"
) -> str:
    """Create a text-based progress bar from percentage.
    
    Args:
        percentage: Percentage value (0-100).
        length: Length of the progress bar in characters.
        fill_char: Character for filled portion.
        empty_char: Character for empty portion.
        
    Returns:
        str: Progress bar string.
    """
    percentage = min(100, max(0, float(percentage)))
    filled = int((percentage / 100) * length)
    empty = length - filled
    
    return fill_char * filled + empty_char * empty


def get_status_emoji(status: str) -> str:
    """Get emoji for VM/container status.
    
    Args:
        status: Status string (running, stopped, etc.).
        
    Returns:
        str: Status emoji.
    """
    status_lower = status.lower()
    
    status_map = {
        "running": "🟢",
        "stopped": "🔴",
        "paused": "🟡",
        "suspended": "🟡",
        "unknown": "⚪",
    }
    
    return status_map.get(status_lower, "⚪")


def get_severity_emoji(severity: str) -> str:
    """Get emoji for alert severity.
    
    Args:
        severity: Severity level (critical, warning, info).
        
    Returns:
        str: Severity emoji.
    """
    severity_lower = severity.lower()
    
    severity_map = {
        "critical": "🔴",
        "high": "🟠",
        "warning": "🟡",
        "info": "🔵",
        "success": "🟢",
    }
    
    return severity_map.get(severity_lower, "ℹ️")
