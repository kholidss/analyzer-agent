import httpx
from app.agent.agent__code_analyzer import *
from app.entity.entity__base_response import AppCtxResponse
from app.entity.entity__code_review import GithubReviewerRequest
from fastapi import BackgroundTasks
from fastapi.concurrency import run_in_threadpool
import asyncio
import structlog

from app.logger import AppCtxLogger


class CodeReviewService:
    def __init__(self, code_analize_agent: CodeAnalyzer):
        self.code_analize_agent = code_analize_agent

    async def github_reviewer(self, request: GithubReviewerRequest, background_tasks: BackgroundTasks):
        lg = AppCtxLogger()

        lg.field("sopo", "Jarwo")
        lg.field("abdul", "Manap")

        ctxResp = AppCtxResponse()
        headers = {
            "Authorization": f"Bearer {request.token}",
            "Accept": "application/vnd.github+json"
        }

        try:
            async with httpx.AsyncClient() as client:
                pr_meta_resp, files_resp = await asyncio.gather(
                    client.get(f"https://api.github.com/repos/{request.repository}/pulls/{request.pr_number}", headers=headers),
                    client.get(f"https://api.github.com/repos/{request.repository}/pulls/{request.pr_number}/files", headers=headers),
                )
                pr_meta = pr_meta_resp.json()
                files = files_resp.json()

            title = pr_meta.get("title", "")
            body = pr_meta.get("body", "")

            patch_text = "\n\n".join(
                f"### {f['filename']}\n{f.get('patch', '[no diff]')}" for f in files if f.get("patch")
            )
        except Exception as e:
            lg.error("call github api got errpr", error=e)
            return ctxResp.with_code(500).json()

        background_tasks.add_task(self.background_analizer_code_process, title, body, patch_text, request.repository, request.pr_number)
        lg.info("success processed task agent analizer code")
        return ctxResp.with_code(201).with_data({"status": "processed"}).json()


    async def background_analizer_code_process(self, title: str, body: str, changes_code: str, repository_name: str, pr_number: int, repository_type: str = "github"):
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