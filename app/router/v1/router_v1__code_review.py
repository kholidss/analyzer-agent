from dependency_injector.wiring import Provide
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject

from app.core.container import Container
from app.entity.entity__code_review import *
from app.service.service__code_review import *

path_code_review = APIRouter(
    prefix="/code-review",
)

@path_code_review.post("/github")
@inject
async def github_reviewer(req: GithubReviewerRequest, background_tasks: BackgroundTasks, service: CodeReviewService = Depends(Provide[Container.code_review_svc])):
    try:
        return await service.github_reviewer(req, background_tasks)
    except Exception as e:
        ctxResp = AppCtxResponse()
        return ctxResp.with_code(500).json()

