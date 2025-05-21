from app.agent.agent__code_analyzer import *
from app.connector.connector__github_api import *
from app.core.config import Config
from app.entity.entity__base_response import AppCtxResponse
from fastapi import BackgroundTasks

from app.entity.entity__web_crawl import CityDensityData, CityDensityTable, SingleWebCrawlRequest
from app.logger import AppCtxLogger
from app.transform import class_to_dict
from app.worker.worker__processs_web_crawler import WebCrawlerWorker, TaskWebCrawlerPayload
from app.worker.worker__process_code_analyzer import *
from fastapi.concurrency import run_in_threadpool
from app.util.context import *
from bs4 import BeautifulSoup, Comment
import undetected_chromedriver as uc
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class WebCrawlService:
    def __init__(self, cfg: Config, extract_markdown_to_json_worker: WebCrawlerWorker):
        self.cfg = cfg
        self.extract_markdown_to_json_worker = extract_markdown_to_json_worker

    async def single_web_crawl(self, request: SingleWebCrawlRequest, background_tasks: BackgroundTasks):
        lg = AppCtxLogger()
        lg.event_name("ServiceSingleWebCrawl")
        lg.field("req", class_to_dict(request))
        ctxResp = AppCtxResponse()

        try:
            worker_payload = TaskWebCrawlerPayload( # Ensure this line is present
                target_url=request.target_url,
                json_result_format=request.json_result_format,
                clue=request.clue,
                current_transaction_attempt=request.current_transaction_attempt,
                max_retry=request.max_retry,
            )
            background_tasks.add_task(run_in_threadpool, self.extract_markdown_to_json_worker.task_single_crawl, worker_payload)

        except Exception as e:
            lg.error("error crawl", error=e)
            return ctxResp.with_code(500).json()

        lg.info("success processed single web data crawler")
        return ctxResp.with_code(201).with_data({"status": "processed"}).json()
