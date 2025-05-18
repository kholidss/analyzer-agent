from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import config, get_config
from app.core.container import Container
from app.middleware.middleware__request_id import RequestContextMiddleware
from app.telegram.telegram__listener import TelegramAssistantListener
from app.util.class_object import singleton
from app.router.v1.base_router import routers as v1_route
from contextlib import asynccontextmanager
import asyncio


@singleton
class AppContext:
    def __init__(self):
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            cfg = get_config()
            bot = TelegramAssistantListener(cfg=cfg)
            asyncio.create_task(bot.run())
            yield

        # set app default
        self.app = FastAPI(
            title=config.APP_NAME,
            lifespan=lifespan
        )

        # reques_id middlewar
        self.app.add_middleware(RequestContextMiddleware)

        # set db and container
        self.container = Container()
        # self.db = self.container.db()
        # self.db.create_database()

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
            return "service is running"

        self.app.include_router(v1_route, prefix="/api/v1")


app_creator = AppContext()
app = app_creator.app
container = app_creator.container

