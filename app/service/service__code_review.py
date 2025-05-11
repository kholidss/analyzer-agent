from app.agent.agent__code_analyzer import *
from app.connector.connector__github_api import *
from app.entity.entity__base_response import AppCtxResponse
from app.entity.entity__code_review import GithubReviewerRequest
from fastapi import BackgroundTasks
import anyio

from app.logger import AppCtxLogger
from app.transform import class_to_dict
from app.worker.worker__process_code_analyzer import *
from fastapi.concurrency import run_in_threadpool


class CodeReviewService:
    def __init__(self, github_api_conn: GithubAPIConnector, code_analyzer_worker: CodeAnalyzerWorker):

        self.github_api_conn = github_api_conn
        self.code_analyzer_worker = code_analyzer_worker

    async def github_reviewer(self, request: GithubReviewerRequest, background_tasks: BackgroundTasks):
        lg = AppCtxLogger()
        lg.field("req", class_to_dict(request))
        ctxResp = AppCtxResponse()

        try:
            resp_github_api = await self.github_api_conn.get_pr_meta(GetPRMetaPayload(request.repository,request.pr_number,request.token))
        except Exception as e:
            lg.error("call github api got error", error=e)
            return ctxResp.with_code(500).json()
        
        worker_payload = TaskAnalyzerCodePayload(
            title=resp_github_api.title,
            body=resp_github_api.body,
            changes_code=resp_github_api.patch_text,
            repo_name=request.repository,
            repo_type="github",
            pr_number=request.pr_number
        )

        background_tasks.add_task(run_in_threadpool, self.code_analyzer_worker.task_analizer_code, worker_payload)

        lg.info("success processed task agent analizer code")
        return ctxResp.with_code(201).with_data({"status": "processed"}).json()
