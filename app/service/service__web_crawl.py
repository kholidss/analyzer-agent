from app.agent.agent__code_analyzer import *
from app.connector.connector__github_api import *
from app.core.config import Config
from app.entity.entity__base_response import AppCtxResponse
from fastapi import BackgroundTasks

from app.entity.entity__web_crawl import CityDensityData, CityDensityTable, SingleWebCrawlRequest
from app.logger import AppCtxLogger
from app.transform import class_to_dict
from app.worker.worker__extract_markdown_to_json import TransformToJSONWorker, TaskTransformToJSONPayload
from app.worker.worker__process_code_analyzer import *
from fastapi.concurrency import run_in_threadpool
from app.util.context import *
from bs4 import BeautifulSoup, Comment
import undetected_chromedriver as uc


class WebCrawlService:
    def __init__(self, cfg: Config, extract_markdown_to_json_worker: TransformToJSONWorker):
        self.cfg = cfg
        self.extract_markdown_to_json_worker = extract_markdown_to_json_worker

    async def single_web_crawl(self, request: SingleWebCrawlRequest, background_tasks: BackgroundTasks):
        lg = AppCtxLogger()
        lg.event_name("ServiceSingleWebCrawl")
        lg.field("req", class_to_dict(request))
        ctxResp = AppCtxResponse()

        try:
            options = uc.ChromeOptions()
            options.add_argument("--start-maximized")

            driver = uc.Chrome(options=options, headless=True)
            driver.get(request.target_url)

            # Wait until finish load
            driver.implicitly_wait(15)

            html = driver.page_source
            driver.quit()
            soup = BeautifulSoup(html, "html.parser")

            # 1. Delete unused element
            for tag in soup(["script", "style", "img", "meta", "link", "noscript"]):
                tag.decompose()

            # 2. Hapus komentar HTML
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            for tag in soup.find_all():
                if not tag.get_text(strip=True):  # Tidak ada teks bermakna
                    tag.decompose()

            cleaned_html = soup.prettify()

            print(cleaned_html)

            worker_payload = TaskTransformToJSONPayload(
                source_type="html",
                source=cleaned_html,
                json_result=request.json_result,
                clue=request.clue
            )
            background_tasks.add_task(run_in_threadpool, self.extract_markdown_to_json_worker.task_transform_to_json, worker_payload)

        except Exception as e:
            lg.error("error crawl", error=e)
            return ctxResp.with_code(500).json()
        
        

        lg.info("success processed single web data crawler")
        return ctxResp.with_code(201).with_data({"status": "processed"}).json()

def parse_number(text: str) -> float:
    return float(text.replace('.', '').replace(',', '.'))

def parse_int(text: str) -> int:
    return int(text.replace('.', '').strip())

def transform_city_density_table(raw_data: dict) -> CityDensityTable:
    result = []
    for row in raw_data["rows"]:
        result.append(CityDensityData(
            no=int(row[0]),
            city=row[1],
            province=row[2],
            area_km2=parse_number(row[3]),
            population_2023=parse_int(row[4]),
            density_per_km2=parse_int(row[5]),
            references=row[6] if len(row) > 6 else None
        ))
    return CityDensityTable(rows=result)