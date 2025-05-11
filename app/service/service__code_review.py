import httpx
from app.agent.agent__code_analyzer import *
from app.connector.connector__github_api import *
from app.core.config import config
from app.entity.entity__base_response import AppCtxResponse
from app.entity.entity__code_review import GithubReviewerRequest
from fastapi import BackgroundTasks
from fastapi.concurrency import run_in_threadpool
import asyncio

from app.logger import AppCtxLogger
from app.transform import class_to_dict


class CodeReviewService:
    def __init__(self, code_analize_agent: CodeAnalyzer, github_api_conn: GithubAPIConnector):
        self.code_analize_agent = code_analize_agent
        self.github_api_conn = github_api_conn

    async def github_reviewer(self, request: GithubReviewerRequest, background_tasks: BackgroundTasks):
        lg = AppCtxLogger()
        lg.field("req", class_to_dict(request))

        ctxResp = AppCtxResponse()
        headers = {
            "Authorization": f"Bearer {request.token}",
            "Accept": "application/vnd.github+json"
        }

        try:
            resp_github_api = await self.github_api_conn.get_pr_meta(GetPRMetaPayload(request.repository,request.pr_number,request.token))
        except Exception as e:
            lg.error("call github api got error", error=e)
            return ctxResp.with_code(500).json()

        background_tasks.add_task(self._background_analizer_code_process, resp_github_api.title, resp_github_api.body, resp_github_api.patch_text, request.repository, request.pr_number)
        lg.info("success processed task agent analizer code")
        return ctxResp.with_code(201).with_data({"status": "processed"}).json()


    async def _background_analizer_code_process(self, title: str, body: str, changes_code: str, repository_name: str, pr_number: int, repository_type: str = "github"):
        print("⏳ Start background analyzer code task...")
        def sync_llm_eval():
            self.code_analize_agent.set_prompt(type="evaluate")
            result = self.code_analize_agent.exec_evaluate(ParamCodeAnalyzerEvaluate(
                pr_title=title,
                pr_body=body,
                pr_patch=changes_code
            ))
            return f"Request Link: {build_request_changes_link(repository_type, repository_name, pr_number)}\n\n{result}"

        result = await run_in_threadpool(sync_llm_eval)
        print("result ==>>> ", result)


def build_request_changes_link(repository_type: str = "github", repository_name: str = "", pr_number: int = 0) -> str:
    if repository_type == "github":
        return f"https://github.com/{repository_name}/pull/{pr_number}"
    
    return ""