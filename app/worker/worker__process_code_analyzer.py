from dataclasses import dataclass
import re

from app.agent.agent__code_analyzer import *
from app.logger import AppCtxLogger

from app.connector.connector__github_api import CommentOnPRPayload, GithubAPIConnector


@dataclass
class TaskAnalyzerCodePayload:
    title: str
    body: str
    author: str
    changes_code: str
    repo_name: str
    pr_number: int
    access_token: str
    repo_type: str = "github"

@dataclass
class GetPRMetaResponse:
    title: str
    body: str
    patch_text: str

class CodeAnalyzerWorker():
    def __init__(self, code_analize_agent: CodeAnalyzer, github_api_conn: GithubAPIConnector):
        self.code_analize_agent = code_analize_agent
        self.github_api_conn = github_api_conn

    def task_analizer_code(self, payload: TaskAnalyzerCodePayload):
        lg = AppCtxLogger()
        lg.event_name("TaskAnalizerCode")
        lg.field("payload.repo_name", payload.repo_name)
        lg.field("payload.pr_number", payload.pr_number)

        self.code_analize_agent.set_prompt(type="evaluate")
        evaluated_result = self.code_analize_agent.exec_evaluate(CodeAnalyzerEvaluateParam(
            pr_title=payload.title,
            pr_body=payload.body,
            pr_patch=payload.changes_code
        ))

        result = f"Changes link: {self._build_request_changes_link(payload)}\n"
        result += f"Authored by: {payload.author}\n\n"
        result += f"{evaluated_result}"

        print("result ===<< ", result)

        comment_pr_payload = CommentOnPRPayload(repo_name=payload.repo_name, pr_number=payload.pr_number, token=payload.access_token, description=result)

        # self.github_api_conn.do_comment_on_pr(comment_pr_payload)
    
    def _build_request_changes_link(self, payload: TaskAnalyzerCodePayload) -> str:
        if payload.repo_type == "github":
            return f"https://github.com/{payload.repo_name}/pull/{payload.pr_number}"
        return ""
