import tempfile
from app.agent.agent__code_analyzer import *
from app.connector.connector__github_api import *
from app.entity.entity__base_response import AppCtxResponse
from fastapi import BackgroundTasks

from app.entity.entity_cv_evaluate import CVEvaluateFromPDFRequest
from app.logger import AppCtxLogger
from app.worker.worker__process_code_analyzer import *
from fastapi.concurrency import run_in_threadpool
from app.util.context import *
from app.worker.worker__process_cv_evaluate import *
from app.worker.worker__process_solving_exam import *


class CVEvaluateService:
    def __init__(self, cv_evaluate_worker: CVEvaluateWorker):
        self.cv_evaluate_worker = cv_evaluate_worker

    async def cv_evaluate_from_pdf(self, request: CVEvaluateFromPDFRequest, background_tasks: BackgroundTasks):
        ctxResp = AppCtxResponse()
        lg = AppCtxLogger()
        lg.event_name("ServiceCVEvaluateFromPDF")
        
        lg.field("request.file_name", request.pdf_file.filename)
        lg.field("request.result_method", request.result_method)

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


        worker_payload = TaskCVEvaluateWorkerFromPDFPayload(
            temp_pdf_path=tmp_path,
            result_method=request.result_method
        )
        background_tasks.add_task(run_in_threadpool, self.cv_evaluate_worker.task_cv_evaluate_from_pdf, worker_payload)

        lg.info("success processed task agent solving exam pdf")
        return ctxResp.with_code(201).with_data({"status": "processed"}).json()

