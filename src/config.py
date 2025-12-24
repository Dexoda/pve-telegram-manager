"""Configuration module for PVE Telegram Manager."""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for bot settings."""
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    ADMIN_IDS: List[int] = [
        int(id_.strip()) 
        for id_ in os.getenv("ADMIN_IDS", "").split(",") 
        if id_.strip()
    ]
    
    # Proxmox Configuration
    PVE_HOST: str = os.getenv("PVE_HOST", "")
    PVE_PORT: int = int(os.getenv("PVE_PORT", "8006"))
    PVE_USER: str = os.getenv("PVE_USER", "root@pam")
    PVE_TOKEN_NAME: str = os.getenv("PVE_TOKEN_NAME", "")
    PVE_TOKEN_VALUE: str = os.getenv("PVE_TOKEN_VALUE", "")
    PVE_VERIFY_SSL: bool = os.getenv("PVE_VERIFY_SSL", "false").lower() == "true"
    
    # SSH Configuration
    SSH_HOST: str = os.getenv("SSH_HOST", "")
    SSH_PORT: int = int(os.getenv("SSH_PORT", "22"))
    SSH_USER: str = os.getenv("SSH_USER", "root")
    SSH_PASSWORD: str = os.getenv("SSH_PASSWORD", "")
    SSH_KEY_PATH: str = os.getenv("SSH_KEY_PATH", "")
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/bot.db")
    
    # Electricity Configuration (Almaty, Kazakhstan)
    ELECTRICITY_RATE: float = float(os.getenv("ELECTRICITY_RATE", "21.80"))
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration parameters."""
        errors = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if not cls.ADMIN_IDS:
            errors.append("ADMIN_IDS is required")
        
        if not cls.PVE_HOST:
            errors.append("PVE_HOST is required")
        
        if not cls.PVE_TOKEN_NAME:
            errors.append("PVE_TOKEN_NAME is required")
        
        if not cls.PVE_TOKEN_VALUE:
            errors.append("PVE_TOKEN_VALUE is required")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")


# Create a singleton instance
config = Config()
