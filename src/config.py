"""
Configuration module for Proxmox Telegram Bot.
Loads environment variables and provides centralized configuration.
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for bot settings."""
    
    # Telegram Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: List[int] = [
        int(admin_id.strip()) 
        for admin_id in os.getenv("ADMIN_IDS", "").split(",") 
        if admin_id.strip()
    ]
    
    # Proxmox API Configuration
    PVE_HOST: str = os.getenv("PVE_HOST", "")
    PVE_USER: str = os.getenv("PVE_USER", "root@pam")
    PVE_TOKEN_NAME: str = os.getenv("PVE_TOKEN_NAME", "")
    PVE_TOKEN_VALUE: str = os.getenv("PVE_TOKEN_VALUE", "")
    PVE_VERIFY_SSL: bool = os.getenv("PVE_VERIFY_SSL", "False").lower() == "true"
    
    # SSH Configuration
    SSH_HOST: str = os.getenv("SSH_HOST", "")
    SSH_USER: str = os.getenv("SSH_USER", "root")
    SSH_KEY_PATH: str = os.getenv("SSH_KEY_PATH", "/root/.ssh/id_rsa")
    SSH_PORT: int = int(os.getenv("SSH_PORT", "22"))
    
    # Electricity Tariff (Almaty, Kazakhstan)
    TARIFF_STEP_1: float = float(os.getenv("TARIFF_STEP_1", "23.21"))
    TARIFF_STEP_2: float = float(os.getenv("TARIFF_STEP_2", "28.50"))
    TARIFF_STEP_3: float = float(os.getenv("TARIFF_STEP_3", "35.00"))
    CURRENCY: str = os.getenv("CURRENCY", "KZT")
    
    # Database Configuration
    DB_PATH: str = os.getenv("DB_PATH", "./data/bot.db")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "./data/bot_usage.log")
    
    # Alert Configuration
    ALERT_HIGH_LOAD_THRESHOLD: int = int(os.getenv("ALERT_HIGH_LOAD_THRESHOLD", "90"))
    ALERT_HIGH_LOAD_DURATION: int = int(os.getenv("ALERT_HIGH_LOAD_DURATION", "300"))
    ALERT_CHECK_INTERVAL: int = int(os.getenv("ALERT_CHECK_INTERVAL", "60"))
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration parameters."""
        required_fields = {
            "BOT_TOKEN": cls.BOT_TOKEN,
            "ADMIN_IDS": cls.ADMIN_IDS,
            "PVE_HOST": cls.PVE_HOST,
            "PVE_TOKEN_NAME": cls.PVE_TOKEN_NAME,
            "PVE_TOKEN_VALUE": cls.PVE_TOKEN_VALUE,
        }
        
        missing = [key for key, value in required_fields.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")


# Create config instance
config = Config()
