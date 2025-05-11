from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import config
from app.core.container import Container
from app.util.class_object import singleton
from app.router.v1.base_router import routers as v1_route


@singleton
class AppContext:
    def __init__(self):
        # set app default
        self.app = FastAPI(
            title=config.APP_NAME,
        )

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

