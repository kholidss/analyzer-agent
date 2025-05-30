from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from app.bootstrap.bootstrap__postgres import PersistencePostgreSQL
from app.core.config import config, get_config
from app.core.container import Container
from app.middleware.middleware__request_id import RequestContextMiddleware
from app.telegram.telegram__listener import TelegramAssistantListener
from app.util.class_object import singleton
from app.router.v1.base_router import routers as v1_route

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BoostrapTelegramBot:
    def __init__(self, cfg, db):
        self.bot_instance = None
        self.bot_task = None
        self.cfg = cfg
        self.db = db
        
    async def start(self):
        self.bot_instance = TelegramAssistantListener(cfg=self.cfg, db=self.db)
        self.bot_task = asyncio.create_task(self.bot_instance.run())
        logger.info("Telegram bot task created")
        
    async def stop(self):
        if self.bot_task:
            self.bot_task.cancel()
            try:
                await self.bot_task
            except asyncio.CancelledError:
                logger.info("Bot task cancelled")
    
    @property
    def is_running(self):
        return self.bot_instance and self.bot_instance._running


class BootstrapDatabase:
    def __init__(self, cfg):
        self.db_instance = None
        self.cfg = cfg
        
    async def connect(self):
        self.db_instance = PersistencePostgreSQL(self.cfg)
        await self.db_instance.connect()
        logger.info("Database connection established")
        return self.db_instance
        
    async def close(self):
        if self.db_instance:
            await self.db_instance.close()
            logger.info("Database connection closed")


class AppLifespanManager:
    def __init__(self):
        self.db_manager = None
        self.bot_manager = None
        self.container = Container()
        
    async def startup(self, app: FastAPI):
        """Initialize application components on startup"""
        cfg = get_config()
        
        # Initialize database
        self.db_manager = BootstrapDatabase(cfg)
        db_instance = await self.db_manager.connect()
        
        # Set up dependency injection
        self.container.db.override(db_instance)
        app.state.container = self.container
        
        # Start Telegram bot
        self.bot_manager = BoostrapTelegramBot(cfg, db_instance)
        await self.bot_manager.start()
        
    async def shutdown(self):
        logger.info("Shutting down application...")
        
        # Stop Telegram bot
        if self.bot_manager:
            await self.bot_manager.stop()
            logger.info("Telegram bot assistant closed")
        
        # Close database connections
        if self.db_manager:
            await self.db_manager.close()
            logger.info("Database connection closed")
            
        logger.info("Application shutdown complete")
        
    def create_lifespan_context(self):
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            try:
                await self.startup(app)
                yield
            except Exception as e:
                logger.error(f"Error during startup: {e}")
                raise
            finally:
                await self.shutdown()
                
        return lifespan


class RouteManager:
    def __init__(self, app: FastAPI, bot_manager: BoostrapTelegramBot):
        self.app = app
        self.bot_manager = bot_manager
        
    def register_routes(self):
        """Healthcheck registry routes"""
        # Root endpoint
        @self.app.get("/")
        def root():
            return {
                "message": "service is running", 
                "bot_status": "active" if self.bot_manager.is_running else "inactive"
            }

        # Health check endpoint
        @self.app.get("/health")
        def health():
            return {
                "status": "healthy",
                "bot_running": self.bot_manager.is_running
            }
        
        # Include API routes
        self.app.include_router(v1_route, prefix="/api/v1")


@singleton
class AppContext:
    def __init__(self):
        # Initialize managers
        self.lifespan_manager = AppLifespanManager()
        
        # Create FastAPI app with lifespan
        self.app = FastAPI(
            title=config.APP_NAME,
            lifespan=self.lifespan_manager.create_lifespan_context()
        )
        
        # Add middleware
        self.app.add_middleware(RequestContextMiddleware)
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self.route_manager = RouteManager(self.app, self.lifespan_manager.bot_manager)
        self.route_manager.register_routes()
        
        # Make container accessible
        self.container = self.lifespan_manager.container


# Create application instance
app_creator = AppContext()
app = app_creator.app
container = app_creator.container
