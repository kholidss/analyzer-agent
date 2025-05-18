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
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pyvirtualdisplay import Display


class WebCrawlService:
    def __init__(self, cfg: Config, extract_markdown_to_json_worker: TransformToJSONWorker):
        self.cfg = cfg
        self.extract_markdown_to_json_worker = extract_markdown_to_json_worker
        self.display = Display(visible=0, size=(1920, 1080))
        self.display.start()

    async def single_web_crawl(self, request: SingleWebCrawlRequest, background_tasks: BackgroundTasks):
        lg = AppCtxLogger()
        lg.event_name("ServiceSingleWebCrawl")
        lg.field("req", class_to_dict(request))
        ctxResp = AppCtxResponse()

        try:
            options = uc.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_argument("--lang=en-US")
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )

            driver = uc.Chrome(options=options, headless=False)
            driver.get(request.target_url)

            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(5)

            driver.implicitly_wait(15)

            # Scroll down 2x to load lazyload
            scroll_pause_time = 3
            for _ in range(2):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause_time)

            html = driver.page_source

            driver.quit()
            self.display.stop()

            soup = BeautifulSoup(html, "html.parser")

            # Remove specific HTML tag
            for tag in soup(["script", "style", "img", "meta", "link", "noscript"]):
                tag.decompose()

            # Remove A with property HREF HTML tag
            for a in soup.find_all("a", href=True):
                a.unwrap()

            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            for tag in soup.find_all():
                if not tag.get_text(strip=True):
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
            try:
                self.display.stop()
            except Exception:
                pass
            return ctxResp.with_code(500).json()

        lg.info("success processed single web data crawler")
        return ctxResp.with_code(201).with_data({"status": "processed"}).json()
