from dataclasses import dataclass
import asyncio

from app.connector.base_connector import BaseConnector
import httpx

from app.core.config import config

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

class GithubAPIConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__()
        self.base_url: str = config.GITHUB_API_BASE_URL

    async def get_pr_meta(self, payload: GetPRMetaPayload) -> GetPRMetaResponse:
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
            patch_text=patch_text
        )
        return res
