from dependency_injector import containers, providers

from app.agent.agent__code_analyzer import CodeAnalyzer
from app.agent.agent__cv_evaluator import CVEvaluator
from app.agent.agent__solving_exam import SolvingExam
from app.connector.connector__github_api import GithubAPIConnector
from app.core.config import config, get_config
from app.pkg.pkg__google_doc import GoogleDocPkg
from app.service.service__code_review import CodeReviewService
from app.service.service__cv_evaluate import CVEvaluateService
from app.service.service__solving_exam import SolvingExamService
from app.worker.worker__process_code_analyzer import CodeAnalyzerWorker
from app.worker.worker__process_cv_evaluate import CVEvaluateWorker
from app.worker.worker__process_solving_exam import SolvingExamWorker


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.router.v1.router_v1__code_review",
            "app.router.v1.router_v1__solve",
            "app.router.v1.router_v1__evaluate",
        ]
    )

    cfg = get_config()
    # db = providers.Singleton(Database, db_url=configs.DATABASE_URI)

    # Connector
    github_api_conn = providers.Singleton(GithubAPIConnector)

    # Pkg
    google_doc_pkg = providers.Singleton(GoogleDocPkg,path_service_account="service_account.json")


    # LLM Agent
    code_analyzer_agent = providers.Singleton(CodeAnalyzer, model_name=config.LLM_GENERAL_MODEL, mode=config.LLM_MODE, base_url=config.LLM_API_BASE_URL, api_key=config.LLM_API_API_KEY)
    solving_exam_agent = providers.Singleton(SolvingExam, model_name=config.LLM_GENERAL_MODEL, mode=config.LLM_MODE, base_url=config.LLM_API_BASE_URL, api_key=config.LLM_API_API_KEY)
    cv_evaluator_agent = providers.Singleton(CVEvaluator, model_name=config.LLM_GENERAL_MODEL, mode=config.LLM_MODE, base_url=config.LLM_API_BASE_URL, api_key=config.LLM_API_API_KEY)

    # Worker dispatcher
    code_analyzer_worker = providers.Singleton(CodeAnalyzerWorker, code_analize_agent=code_analyzer_agent, github_api_conn=github_api_conn)
    solving_exam_worker = providers.Singleton(SolvingExamWorker, solving_exam_agent=solving_exam_agent, google_doc_pkg=google_doc_pkg)
    cv_evaluate_worker = providers.Singleton(CVEvaluateWorker, cv_evaluator_agent=cv_evaluator_agent)

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
    cv_evalute_svc = providers.Singleton(
        CVEvaluateService,
        cv_evaluate_worker=cv_evaluate_worker
    )