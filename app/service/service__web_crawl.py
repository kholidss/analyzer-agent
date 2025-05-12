from app.agent.agent__code_analyzer import *
from app.connector.connector__github_api import *
from app.core.config import Config, get_config
from app.entity.entity__base_response import AppCtxResponse
from fastapi import BackgroundTasks

from app.entity.entity__web_crawl import CityDensityData, CityDensityTable, IndonesianCitizenCrawlResponse, SingleWebCrawlRequest
from app.logger import AppCtxLogger
from app.transform import class_to_dict
from app.worker.worker__process_code_analyzer import *
from fastapi.concurrency import run_in_threadpool
from app.util.context import *
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
import json


class WebCrawlService:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    async def single_web_crawl(self, request: SingleWebCrawlRequest, background_tasks: BackgroundTasks):
        lg = AppCtxLogger()
        lg.event_name("ServiceSingleWebCrawl")
        lg.field("req", class_to_dict(request))
        ctxResp = AppCtxResponse()

        try:
            crawl_config = CrawlerRunConfig(
                exclude_external_images=True,
                cache_mode=CacheMode.BYPASS,
                table_score_threshold=2,
            )

            browser_cfg = BrowserConfig(headless=True)

            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                result = await crawler.arun(
                    url=request.target_url,
                    config=crawl_config
                )

                if result.success:

                    # table = transform_table_data(result.tables[0])
                    parsed_table = transform_city_density_table(result.tables[1])
                    print("parsed ==>>> ", parsed_table)
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