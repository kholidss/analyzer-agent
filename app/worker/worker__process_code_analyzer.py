from dataclasses import dataclass

from fastapi.concurrency import run_in_threadpool

from app.agent.agent__code_analyzer import *


@dataclass
class TaskAnalyzerCodePayload:
    title: str
    body: str
    changes_code: str
    repo_name: str
    pr_number: int
    repo_type: str = "github"

@dataclass
class GetPRMetaResponse:
    title: str
    body: str
    patch_text: str

class CodeAnalyzerWorker():
    def __init__(self, code_analize_agent: CodeAnalyzer):
        self.code_analize_agent = code_analize_agent

    async def task_analizer_code(self, payload: TaskAnalyzerCodePayload):
        print("⏳ Start background analyzer code task...")
        def sync_llm_eval():
            self.code_analize_agent.set_prompt(type="evaluate")
            result = self.code_analize_agent.exec_evaluate(CodeAnalyzerEvaluateParam(
                pr_title=payload.title,
                pr_body=payload.body,
                pr_patch=payload.changes_code
            ))
            return f"Request Link: {self._build_request_changes_link(payload)}\n\n{result}"

        result = await run_in_threadpool(sync_llm_eval)
        
        print("result ==>>> ", result)
    
    def _build_request_changes_link(self, payload: TaskAnalyzerCodePayload) -> str:
        if payload.repo_type == "github":
            return f"https://github.com/{payload.repo_name}/pull/{payload.pr_number}"
        return ""