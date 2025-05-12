import tempfile
from app.agent.agent__code_analyzer import *
from app.connector.connector__github_api import *
from app.entity.entity__base_response import AppCtxResponse
from fastapi import BackgroundTasks

from app.entity.entity_solving_exam import SolvingExamFromPDFRequest
from app.logger import AppCtxLogger
from app.worker.worker__process_code_analyzer import *
from fastapi.concurrency import run_in_threadpool
from app.util.context import *
from app.worker.worker__process_solving_exam import *


class SolvingExamService:
    def __init__(self, solving_exam_worker: SolvingExamWorker):
        self.solving_exam_worker = solving_exam_worker

    async def solving_exam_from_pdf(self, request: SolvingExamFromPDFRequest, background_tasks: BackgroundTasks):
        ctxResp = AppCtxResponse()
        lg = AppCtxLogger()
        lg.event_name("ServiceSolvingExamFromPDF")
        
        lg.field("request.file_name", request.pdf_file.filename)

        try:
            file_content = await request.pdf_file.read()
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(file_content)
                tmp.flush()
                tmp_path = tmp.name
        except Exception as e:
            lg.error("write pdf to temporary file got error", error=e)
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            return ctxResp.with_code(500).json()


        worker_payload = TaskSolvingExamFromPDFPayload(
            temp_pdf_path=tmp_path,
            result_doc_title=request.result_doc_title
        )
        background_tasks.add_task(run_in_threadpool, self.solving_exam_worker.task_solving_exam_from_pdf, worker_payload)

        lg.info("success processed task agent solving exam pdf")
        return ctxResp.with_code(201).with_data({"status": "processed"}).json()

