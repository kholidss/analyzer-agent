from dependency_injector.wiring import Provide
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject

from app.core.container import Container
from app.entity.entity__base_response import AppCtxResponse
from app.entity.entity_cv_evaluate import CVEvaluateFromPDFRequest
from app.service.service__cv_evaluate import CVEvaluateService
from fastapi import *

path_evaluate = APIRouter(
    prefix="/evaluate",
)

@path_evaluate.post("/cv-pdf")
@inject
async def cv_evaluate_from_pdf(
    background_tasks: BackgroundTasks,
    pdf_file: UploadFile = File(...),
    result_method: str = Form("default"),
    service: CVEvaluateService = Depends(Provide[Container.cv_evalute_svc])
):
    req = CVEvaluateFromPDFRequest(pdf_file=pdf_file, result_method=result_method)
    try:
        return await service.cv_evaluate_from_pdf(req, background_tasks)
    except Exception as e:
        ctxResp = AppCtxResponse()
        return ctxResp.with_code(500).json()

