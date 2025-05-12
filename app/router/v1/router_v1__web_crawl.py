from dependency_injector.wiring import Provide
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject

from app.core.container import Container
from app.entity.entity__code_review import *
from app.entity.entity__web_crawl import SingleWebCrawlRequest
from app.service.service__code_review import *
from app.service.service__web_crawl import WebCrawlService

path_web_crawl = APIRouter(
    prefix="/web-crawl",
)

@path_web_crawl.post("/single")
@inject
async def github_reviewer(req: SingleWebCrawlRequest, background_tasks: BackgroundTasks, service: WebCrawlService = Depends(Provide[Container.web_crawl_svc])):
    try:
        return await service.single_web_crawl(req, background_tasks)
    except Exception as e:
        ctxResp = AppCtxResponse()
        return ctxResp.with_code(500).json()

