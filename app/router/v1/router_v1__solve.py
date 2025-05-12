from dependency_injector.wiring import Provide
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject

from app.core.container import Container
from app.entity.entity__base_response import AppCtxResponse
from app.entity.entity_solving_exam import SolvingExamFromPDFRequest
from app.service.service__solving_exam import SolvingExamService
from fastapi import *

path_solve = APIRouter(
    prefix="/solve",
)

@path_solve.post("/exam-pdf")
@inject
async def solving_exam_from_pdf(
    background_tasks: BackgroundTasks,
    pdf_file: UploadFile = File(...),
    result_doc_title: str = Form(""),
    service: SolvingExamService = Depends(Provide[Container.solving_exam_svc])
):
    req = SolvingExamFromPDFRequest(pdf_file=pdf_file, result_doc_title=result_doc_title)
    try:
        return await service.solving_exam_from_pdf(req, background_tasks)
    except Exception as e:
        ctxResp = AppCtxResponse()
        return ctxResp.with_code(500).json()

