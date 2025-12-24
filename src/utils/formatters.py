"""Formatters for Telegram messages."""
import re
from typing import Any


def escape_markdown_v2(text: str) -> str:
    """
    Escape special characters for MarkdownV2.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for MarkdownV2
    """
    special_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in special_chars else char for char in str(text))


# Alias for convenience
escape_markdown = escape_markdown_v2


def format_code_block(text: str, language: str = "") -> str:
    """
    Format text as a code block.
    
    Args:
        text: Text to format
        language: Programming language for syntax highlighting
        
    Returns:
        Formatted code block
    """
    if language:
        return f"```{language}\n{text}\n```"
    return f"```\n{text}\n```"


def format_inline_code(text: str) -> str:
    """
    Format text as inline code.
    
    Args:
        text: Text to format
        
    Returns:
        Formatted inline code
    """
    return f"`{text}`"


def format_code(text: str) -> str:
    """
    Format text as inline code for Telegram.
    
    Args:
        text: Text to format
        
    Returns:
        Formatted text
    """
    return f"`{escape_markdown_v2(text)}`"


def format_bold(text: str) -> str:
    """
    Format text as bold for Telegram.
    
    Args:
        text: Text to format
        
    Returns:
        Formatted text
    """
    return f"*{escape_markdown_v2(text)}*"


def format_italic(text: str) -> str:
    """
    Format text as italic for Telegram.
    
    Args:
        text: Text to format
        
    Returns:
        Formatted text
    """
    return f"_{escape_markdown_v2(text)}_"


def format_link(text: str, url: str) -> str:
    """
    Format text as a clickable link for Telegram.
    
    Args:
        text: Link text
        url: URL
        
    Returns:
        Formatted link
    """
    return f"[{escape_markdown_v2(text)}]({url})"


def format_pre(text: str, language: str = "") -> str:
    """
    Format text as preformatted code block.
    
    Args:
        text: Text to format
        language: Programming language for syntax highlighting
        
    Returns:
        Formatted code block
    """
    if language:
        return f"```{language}\n{text}\n```"
    return f"```\n{text}\n```"


def truncate_text(text: str, max_length: int = 4096) -> str:
    """
    Truncate text to fit Telegram message limits.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (default: 4096)
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
