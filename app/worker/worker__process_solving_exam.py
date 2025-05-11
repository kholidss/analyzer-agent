from dataclasses import dataclass

from app.agent.agent__code_analyzer import *
from app.agent.agent__solving_exam import *
from app.logger import AppCtxLogger

from app.connector.connector__github_api import CommentOnPRPayload, GithubAPIConnector
from fastapi import UploadFile
import tempfile

from app.util.pdf import extract_text_from_pdf
import os


@dataclass
class TaskSolvingExamFromPDFPayload:
    temp_pdf_path: str


class SolvingExamFromWorker():
    def __init__(self, solving_exam_agent: SolvingExam):
        self.solving_exam_agent = solving_exam_agent

    def task_solving_exam_from_pdf(self, payload: TaskSolvingExamFromPDFPayload):
        lg = AppCtxLogger()
        lg.event_name("TaskSolvingExamFromPDF")

        try:
            extracted_pdf = extract_text_from_pdf(payload.temp_pdf_path)
            if not extracted_pdf:
                lg.error("could not extract meta text from pdf", error="empty meta pdf")
                return
        except Exception as e:
            lg.error("got error from process extract pdf", error=e)
            return
        
        finally:
            if payload.temp_pdf_path and os.path.exists(payload.temp_pdf_path):
                os.remove(payload.temp_pdf_path)

        print("extracted_pdf ==>>> ", extracted_pdf)
        self.solving_exam_agent.set_prompt(type="answer")
        answer_result = self.solving_exam_agent.exec_answer(SolvingExamParam(
            question=extracted_pdf
        ))

        result = f"{answer_result}"

        lg.info("finished task")
        print(result)

