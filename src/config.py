"""Configuration loader for Proxmox Telegram Bot."""

import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    
    token: str
    admin_ids: List[int]


@dataclass
class ProxmoxConfig:
    """Proxmox API configuration."""
    
    host: str
    user: str
    token_name: str
    token_value: str
    verify_ssl: bool = False


@dataclass
class SSHConfig:
    """SSH connection configuration."""
    
    host: str
    user: str
    key_path: str
    port: int = 22


@dataclass
class TariffConfig:
    """Electricity tariff configuration."""
    
    step_1: float  # 0-150 kWh
    step_2: float  # 150-300 kWh
    step_3: float  # 300+ kWh
    currency: str


@dataclass
class DatabaseConfig:
    """Database configuration."""
    
    path: str


@dataclass
class LoggingConfig:
    """Logging configuration."""
    
    level: str
    file: str


@dataclass
class AlertConfig:
    """Alert system configuration."""
    
    high_load_threshold: int
    high_load_duration: int
    check_interval: int


@dataclass
class Config:
    """Application configuration."""
    
    telegram: TelegramConfig
    proxmox: ProxmoxConfig
    ssh: SSHConfig
    tariff: TariffConfig
    database: DatabaseConfig
    logging: LoggingConfig
    alerts: AlertConfig


def load_config() -> Config:
    """Load configuration from environment variables.
    
    Returns:
        Config: Application configuration object.
        
    Raises:
        ValueError: If required environment variables are missing.
    """
    # Parse admin IDs
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        raise ValueError("ADMIN_IDS environment variable is required")
    
    admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",")]
    
    # Telegram configuration
    telegram = TelegramConfig(
        token=os.getenv("BOT_TOKEN", ""),
        admin_ids=admin_ids
    )
    
    if not telegram.token:
        raise ValueError("BOT_TOKEN environment variable is required")
    
    # Proxmox configuration
    proxmox = ProxmoxConfig(
        host=os.getenv("PVE_HOST", ""),
        user=os.getenv("PVE_USER", "root@pam"),
        token_name=os.getenv("PVE_TOKEN_NAME", ""),
        token_value=os.getenv("PVE_TOKEN_VALUE", "")
    )
    
    if not all([proxmox.host, proxmox.token_name, proxmox.token_value]):
        raise ValueError("Proxmox configuration (PVE_HOST, PVE_TOKEN_NAME, PVE_TOKEN_VALUE) is required")
    
    # SSH configuration
    ssh = SSHConfig(
        host=os.getenv("SSH_HOST", proxmox.host),
        user=os.getenv("SSH_USER", "root"),
        key_path=os.getenv("SSH_KEY_PATH", "/root/.ssh/id_rsa")
    )
    
    # Tariff configuration
    tariff = TariffConfig(
        step_1=float(os.getenv("TARIFF_STEP_1", "23.21")),
        step_2=float(os.getenv("TARIFF_STEP_2", "28.50")),
        step_3=float(os.getenv("TARIFF_STEP_3", "35.00")),
        currency=os.getenv("CURRENCY", "KZT")
    )
    
    # Database configuration
    database = DatabaseConfig(
        path=os.getenv("DB_PATH", "./data/bot.db")
    )
    
    # Logging configuration
    logging = LoggingConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        file=os.getenv("LOG_FILE", "./data/bot_usage.log")
    )
    
    # Alert configuration
    alerts = AlertConfig(
        high_load_threshold=int(os.getenv("ALERT_HIGH_LOAD_THRESHOLD", "90")),
        high_load_duration=int(os.getenv("ALERT_HIGH_LOAD_DURATION", "300")),
        check_interval=int(os.getenv("ALERT_CHECK_INTERVAL", "60"))
    )
    
    return Config(
        telegram=telegram,
        proxmox=proxmox,
        ssh=ssh,
        tariff=tariff,
        database=database,
        logging=logging,
        alerts=alerts
    )
