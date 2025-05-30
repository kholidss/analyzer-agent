from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.bootstrap.bootstrap__postgres import BootstrapPostgres
from app.core.config import config, get_config
from app.core.container import Container
from app.middleware.middleware__request_id import RequestContextMiddleware
from app.telegram.telegram__listener import TelegramAssistantListener
from app.util.class_object import singleton
from app.router.v1.base_router import routers as v1_route
from contextlib import asynccontextmanager
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@singleton
class AppContext:
    def __init__(self):
        self.bot_instance = None
        self.bot_task = None
        self.db_instance = None
        self.container = Container()
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            try:
                cfg = get_config()

                # Init db
                self.db_instance = BootstrapPostgres(cfg)
                await self.db_instance.connect()

                self.container.db.override(self.db_instance)

                app.state.container = self.container
                app.state.db = self.db_instance

                # self.container = Container()
                # self.container.db.override(db_instance)

                self.bot_instance = TelegramAssistantListener(cfg=cfg, db=self.db_instance)
                self.bot_task = asyncio.create_task(self.bot_instance.run())
                logger.info("Telegram bot task created")
                yield
            except Exception as e:
                logger.error(f"Error during startup: {e}")
                raise
            finally:
                # Shutdown
                logger.info("Shutting down application...")
                if self.bot_task:
                    self.bot_task.cancel()
                    try:
                        await self.bot_task
                    except asyncio.CancelledError:
                        logger.info("Bot task cancelled")
                
                # Close DB connection
                if self.db_instance:
                    await self.db_instance.close()
                    logger.info("Database connection closed")

                logger.info("Application shutdown complete")

        # set app default
        self.app = FastAPI(
            title=config.APP_NAME,
            lifespan=lifespan
        )

        # request_id middleware
        self.app.add_middleware(RequestContextMiddleware)

        # set db and container
        self.container = Container()

        # set cors
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # set routes
        @self.app.get("/")
        def root():
            return {"message": "service is running", "bot_status": "active" if self.bot_instance and self.bot_instance._running else "inactive"}

        @self.app.get("/health")
        def health():
            return {
                "status": "healthy",
                "bot_running": self.bot_instance._running if self.bot_instance else False
            }

        self.app.include_router(v1_route, prefix="/api/v1")

app_creator = AppContext()
app = app_creator.app
container = app_creator.container
