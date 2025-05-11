from dependency_injector import containers, providers

from app.agent.agent__code_analyzer import CodeAnalyzer
from app.core.config import config
from app.service.service__code_review import CodeReviewService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.router.v1.router_v1__code_review",
        ]
    )

    # db = providers.Singleton(Database, db_url=configs.DATABASE_URI)
    code_analyzer_agent = providers.Factory(CodeAnalyzer, model_name=config.LLM_MODEL_COMMON)

    code_review_svc = providers.Factory(CodeReviewService, code_analize_agent=code_analyzer_agent)
