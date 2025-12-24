"""
Main bot initialization and startup.
"""
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
from src.handlers import common
from src.handlers import vms
from src.handlers import monitoring
from src.handlers import storage
from src.handlers import finance
from src.handlers import logs
from src.handlers import tools

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE) if config.LOG_FILE else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main bot function."""
    try:
        # Validate configuration
        config.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize database
        db = Database(config.DB_PATH)
        await db.initialize()
        logger.info("Database initialized successfully")
        
        # Initialize Proxmox client
        pve_client = ProxmoxClient(
            host=config.PVE_HOST,
            user=config.PVE_USER,
            token_name=config.PVE_TOKEN_NAME,
            token_value=config.PVE_TOKEN_VALUE,
            verify_ssl=config.PVE_VERIFY_SSL
        )
        logger.info("Proxmox client initialized successfully")
        
        # Test Proxmox connection
        nodes = await pve_client.get_nodes()
        if nodes:
            logger.info(f"Connected to Proxmox: {len(nodes)} node(s) found")
        else:
            logger.warning("Could not retrieve Proxmox nodes, but continuing...")
        
        # Initialize SSH client
        ssh_client = SSHClient(
            host=config.SSH_HOST,
            user=config.SSH_USER,
            key_path=config.SSH_KEY_PATH,
            port=config.SSH_PORT
        )
        logger.info("SSH client initialized successfully")
        
        # Set database and services in handlers
        common.set_database(db)
        vms.set_services(pve_client, db)
        monitoring.set_services(pve_client, ssh_client, db)
        storage.set_services(pve_client, ssh_client, db)
        finance.set_services(db)
        logs.set_services(ssh_client, db)
        tools.set_services(ssh_client, db)
        
        # Initialize bot and dispatcher
        bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
        )
        
        dp = Dispatcher()
        
        # Register routers
        dp.include_router(common.router)
        dp.include_router(vms.router)
        dp.include_router(monitoring.router)
        dp.include_router(storage.router)
        dp.include_router(finance.router)
        dp.include_router(logs.router)
        dp.include_router(tools.router)
        
        # Initialize alert service
        alert_service = AlertService(bot, pve_client)
        await alert_service.start()
        
        logger.info("Bot starting...")
        logger.info(f"Authorized admins: {config.ADMIN_IDS}")
        
        try:
            # Start polling
            await dp.start_polling(bot)
        finally:
            # Stop alert service on shutdown
            await alert_service.stop()
            logger.info("Bot shutdown complete")
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
