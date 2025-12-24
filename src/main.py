"""Main entry point for the Proxmox Telegram Bot."""

import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from src.config import load_config
from src.database import Database
from src.services.proxmox import ProxmoxClient
from src.services.ssh_client import SSHClient
from src.handlers.common import router as common_router, setup_common_router
from src.handlers.vms import router as vms_router, setup_vms_router
from src.handlers.monitoring import router as monitoring_router, setup_monitoring_router
from src.handlers.storage import router as storage_router, setup_storage_router


# Configure logging
def setup_logging(log_level: str, log_file: str):
    """Setup logging configuration.
    
    Args:
        log_level: Logging level (INFO, DEBUG, etc.).
        log_file: Path to log file.
    """
    # Ensure log directory exists
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )


async def main():
    """Main function to run the bot."""
    # Load configuration
    try:
        config = load_config()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    # Setup logging
    setup_logging(config.logging.level, config.logging.file)
    logger = logging.getLogger(__name__)
    logger.info("Starting Proxmox Telegram Bot...")
    
    # Initialize database
    db = Database(config.database.path)
    await db.init_db()
    logger.info("Database initialized")
    
    # Initialize Proxmox client
    try:
        proxmox = ProxmoxClient(
            host=config.proxmox.host,
            user=config.proxmox.user,
            token_name=config.proxmox.token_name,
            token_value=config.proxmox.token_value,
            verify_ssl=config.proxmox.verify_ssl
        )
        logger.info("Proxmox client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Proxmox client: {e}")
        sys.exit(1)
    
    # Initialize SSH client
    try:
        ssh = SSHClient(
            host=config.ssh.host,
            user=config.ssh.user,
            key_path=config.ssh.key_path,
            port=config.ssh.port
        )
        logger.info("SSH client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize SSH client: {e}")
        sys.exit(1)
    
    # Setup handlers with dependencies
    setup_common_router(config, db)
    setup_vms_router(config, db, proxmox)
    setup_monitoring_router(config, db, proxmox, ssh)
    setup_storage_router(config, db, proxmox, ssh)
    logger.info("Handlers initialized")
    
    # Initialize bot and dispatcher
    bot = Bot(token=config.telegram.token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    
    # Register routers
    dp.include_router(common_router)
    dp.include_router(vms_router)
    dp.include_router(monitoring_router)
    dp.include_router(storage_router)
    logger.info("Routers registered")
    
    # Start bot
    try:
        logger.info("Bot started successfully")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
