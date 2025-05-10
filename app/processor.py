import httpx
from pydantic import BaseModel
from fastapi import BackgroundTasks
from fastapi.concurrency import run_in_threadpool

from .llm_agent__code_analyzer import PRAnalyzer, ParamCodeAnalyzerEvaluate


class AnalyzePRPayload(BaseModel):
    repository: str
    pr_number: int
    token: str


async def analizer_github(payload: AnalyzePRPayload, background_tasks: BackgroundTasks) -> dict:
    headers = {
        "Authorization": f"Bearer {payload.token}",
        "Accept": "application/vnd.github+json"
    }

    async with httpx.AsyncClient() as client:
        # Get PR metadata
        pr_meta_resp = await client.get(
            f"https://api.github.com/repos/{payload.repository}/pulls/{payload.pr_number}",
            headers=headers
        )
        pr_meta = pr_meta_resp.json()

        # Get PR code changes
        files_resp = await client.get(
            f"https://api.github.com/repos/{payload.repository}/pulls/{payload.pr_number}/files",
            headers=headers
        )
        files = files_resp.json()

    title = pr_meta.get("title", "")
    body = pr_meta.get("body", "")

    patch_text = "\n\n".join(
        f"### {f['filename']}\n{f.get('patch', '[no diff]')}" for f in files if f.get("patch")
    )

    background_tasks.add_task(background_analizer_code_process, title, body, patch_text)
    return {"status": "processed"}


async def background_analizer_code_process(title: str, body: str, changes_code: str):
    print("⏳ Start background analyzer code task...")

    def sync_llm_eval():
        analyzer = PRAnalyzer()
        analyzer.set_prompt(type="evaluate")
        return analyzer.exec_evaluate(ParamCodeAnalyzerEvaluate(
            pr_title=title,
            pr_body=body,
            pr_patch=changes_code
        ))

    result = await run_in_threadpool(sync_llm_eval)
    print("result ==>>> ", result)
