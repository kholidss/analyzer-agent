from dataclasses import dataclass
import asyncio

from app.connector.base_connector import BaseConnector
import httpx

from app.core.config import config
from app.logger import AppCtxLogger

@dataclass
class GetPRMetaPayload:
    repo_name: str
    pr_number: str
    token: str

@dataclass
class GetPRMetaResponse:
    title: str
    body: str
    patch_text: str
    author: str

@dataclass
class CommentOnPRPayload:
    repo_name: str
    pr_number: str
    token: str
    description: str

class GithubAPIConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__()
        self.base_url: str = config.GITHUB_API_BASE_URL

    async def get_pr_meta(self, payload: GetPRMetaPayload) -> GetPRMetaResponse:
        lg = AppCtxLogger()
        lg.event_name("ConnectorGithubGetPRMeta")
        lg.field("payload.repo_name", payload.repo_name)
        lg.field("payload.pr_number", payload.pr_number)
        
        h = {
            "Authorization": f"Bearer {payload.token}",
            "Accept": "application/vnd.github+json"
        }

        async with httpx.AsyncClient(timeout=self.timeout_second) as client:
                pr_meta_resp, files_resp = await asyncio.gather(
                    client.get(f"{self.base_url}/repos/{payload.repo_name}/pulls/{payload.pr_number}", headers=h),
                    client.get(f"{self.base_url}/repos/{payload.repo_name}/pulls/{payload.pr_number}/files", headers=h),
                )
                pr_meta = pr_meta_resp.json()
                files = files_resp.json()

        patch_text = "\n\n".join(
        f"### {f['filename']}\n{f.get('patch', '[no diff]')}" for f in files if f.get("patch")
            )
        
        res = GetPRMetaResponse(
            title=pr_meta.get("title", ""),
            body=pr_meta.get("body", ""),
            patch_text=patch_text,
            author=pr_meta.get("user", {}).get("login", "[unknown]")
        )

        lg.info("success call github api")

        return res
    
    def do_comment_on_pr(self, payload: CommentOnPRPayload):
        lg = AppCtxLogger()
        lg.event_name("ConnectorGithubDoCommentOnPR")
        lg.field("payload.repo_name", payload.repo_name)
        lg.field("payload.pr_number", payload.pr_number)

        headers = {
            "Authorization": f"Bearer {payload.token}",
            "Accept": "application/vnd.github+json"
        }

        url = f"https://api.github.com/repos/{payload.repo_name}/issues/{payload.pr_number}/comments"
        httpx.post(url, headers=headers, json={"body": payload.description})
        lg.info("success call github api")
