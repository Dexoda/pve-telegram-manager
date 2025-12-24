"""Main entry point for PVE Telegram Manager bot."""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import config
from src.database.db import Database
from src.services.proxmox import ProxmoxClient
from src.services.ssh_client import SSHClient
from src.services.alerts import AlertService

# Import handlers
from src.handlers import common, vms, monitoring, storage, finance, logs, tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Initialize and run the bot."""
    try:
        # Validate configuration
        config.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize database
        db = Database(config.DATABASE_PATH)
        await db.init()
        logger.info("Database initialized")
        
        # Initialize Proxmox client
        proxmox = ProxmoxClient(
            host=config.PVE_HOST,
            port=config.PVE_PORT,
            user=config.PVE_USER,
            token_name=config.PVE_TOKEN_NAME,
            token_value=config.PVE_TOKEN_VALUE,
            verify_ssl=config.PVE_VERIFY_SSL
        )
        logger.info("Proxmox client initialized")
        
        # Initialize SSH client (if configured)
        ssh_client = None
        if config.SSH_HOST and (config.SSH_PASSWORD or config.SSH_KEY_PATH):
            ssh_client = SSHClient(
                host=config.SSH_HOST,
                port=config.SSH_PORT,
                username=config.SSH_USER,
                password=config.SSH_PASSWORD if config.SSH_PASSWORD else None,
                key_path=config.SSH_KEY_PATH if config.SSH_KEY_PATH else None
            )
            logger.info("SSH client initialized")
        else:
            logger.warning("SSH client not configured - some features will be unavailable")
        
        # Initialize bot and dispatcher
        bot = Bot(
            token=config.TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
        )
        dp = Dispatcher()
        
        # Store services in bot data for access in handlers
        dp["db"] = db
        dp["proxmox"] = proxmox
        dp["ssh_client"] = ssh_client
        dp["config"] = config
        
        # Register routers
        dp.include_router(common.router)
        dp.include_router(vms.router)
        dp.include_router(monitoring.router)
        dp.include_router(storage.router)
        dp.include_router(finance.router)
        dp.include_router(logs.router)
        dp.include_router(tools.router)
        
        logger.info("All routers registered")
        
        # Initialize alert service
        alert_service = AlertService(bot, proxmox, db)
        
        # Start alert service in background
        alert_task = asyncio.create_task(alert_service.start())
        logger.info("Alert service started")
        
        # Start polling
        logger.info("Bot started successfully")
        await dp.start_polling(bot)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        if 'db' in locals():
            await db.close()
        if 'alert_task' in locals():
            alert_task.cancel()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
