from dataclasses import dataclass

from app.agent.agent__code_analyzer import *
from app.agent.agent__cv_evaluator import *
from app.agent.agent__solving_exam import *
from app.logger import AppCtxLogger

from app.util.pdf import extract_text_from_pdf
import os


@dataclass
class TaskCVEvaluateWorkerFromPDFPayload:
    temp_pdf_path: str
    result_method: str


class CVEvaluateWorker():
    def __init__(self, cv_evaluator_agent: CVEvaluator):
        self.cv_evaluator_agent = cv_evaluator_agent

    def task_cv_evaluate_from_pdf(self, payload: TaskCVEvaluateWorkerFromPDFPayload):
        lg = AppCtxLogger()
        lg.event_name("TaskCVEvaluateWorkerFromPDF")

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

        self.cv_evaluator_agent.set_prompt(type="answer", analysis_goal=payload.result_method)
        answer_result = self.cv_evaluator_agent.exec_evaluate(CVEvaluatorParam(
            cv_text=extracted_pdf
        ))

        result = f"{answer_result}"

        print("result ==<<< ", result)

        lg.info("finished task")

