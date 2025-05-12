from dataclasses import dataclass
import re

from app.agent.agent__code_analyzer import *
from app.agent.agent__solving_exam import *
from app.logger import AppCtxLogger

from app.pkg.pkg__google_doc import GoogleDocPkg, WriteDocParam
from app.util.pdf import extract_text_from_pdf
import os


@dataclass
class TaskSolvingExamFromPDFPayload:
    temp_pdf_path: str
    result_doc_title: str


class SolvingExamWorker():
    def __init__(self, solving_exam_agent: SolvingExam, google_doc_pkg: GoogleDocPkg):
        self.solving_exam_agent = solving_exam_agent
        self.google_doc_pkg = google_doc_pkg

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

        self.solving_exam_agent.set_prompt(type="answer")
        answer_result = self.solving_exam_agent.exec_answer(SolvingExamParam(
            question=extracted_pdf
        ))

        try:
                wr = self.google_doc_pkg.write_doc(WriteDocParam(content=answer_result, doc_title=payload.result_doc_title))
                result_url = wr.get_result_doc_url_edit()
                print("result_url ===>>> ", result_url)
                lg.info("finished task")
                return
        except Exception as e:
            lg.error("got error from write answer to google doc api", error=e)
            return


