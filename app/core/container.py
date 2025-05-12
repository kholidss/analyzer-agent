from dependency_injector import containers, providers

from app.agent.agent__code_analyzer import CodeAnalyzer
from app.agent.agent__solving_exam import SolvingExam
from app.connector.connector__github_api import GithubAPIConnector
from app.core.config import config
from app.service.service__code_review import CodeReviewService
from app.service.service__solving_exam import SolvingExamService
from app.worker.worker__process_code_analyzer import CodeAnalyzerWorker
from app.worker.worker__process_solving_exam import SolvingExamFromWorker


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.router.v1.router_v1__code_review",
            "app.router.v1.router_v1__solve",
        ]
    )

    # db = providers.Singleton(Database, db_url=configs.DATABASE_URI)

    # Connector
    github_api_conn = providers.Singleton(GithubAPIConnector)

    # LLM Agent
    code_analyzer_agent = providers.Singleton(CodeAnalyzer, model_name=config.LLM_MODEL_COMMON, mode=config.LLM_MODE, base_url=config.LLM_API_BASE_URL, api_key=config.LLM_API_API_KEY)
    solving_exam_agent = providers.Singleton(SolvingExam, model_name=config.LLM_MODEL_COMMON, mode=config.LLM_MODE, base_url=config.LLM_API_BASE_URL, api_key=config.LLM_API_API_KEY)

    # Worker dispatcher
    code_analyzer_worker = providers.Singleton(CodeAnalyzerWorker, code_analize_agent=code_analyzer_agent, github_api_conn=github_api_conn)
    solving_exam_worker = providers.Singleton(SolvingExamFromWorker, solving_exam_agent=solving_exam_agent)

    # Service
    code_review_svc = providers.Singleton(
        CodeReviewService,
        github_api_conn=github_api_conn,
        code_analyzer_worker=code_analyzer_worker
    )
    solving_exam_svc = providers.Singleton(
        SolvingExamService,
        solving_exam_worker=solving_exam_worker
    )
