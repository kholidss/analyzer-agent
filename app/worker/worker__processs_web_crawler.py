from dataclasses import dataclass

from app.agent.agent__code_analyzer import *
from app.agent.agent__transform_to_json import TransformToJSON, TransformToJSONParam
from app.logger import AppCtxLogger

from app.connector.connector__github_api import CommentOnPRPayload, GithubAPIConnector
import json
import time
from bs4 import BeautifulSoup, Comment
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display


@dataclass
class TaskWebCrawlerPayload:
    target_url: str
    json_result_format: str
    clue: str
    json_result_format: str
    clue: str
    current_transaction_attempt: int = 1
    max_retry: int = 3


class WebCrawlerWorker():
    def __init__(self, extract_markdown_to_json_agent: TransformToJSON):
        self.extract_markdown_to_json_agent = extract_markdown_to_json_agent

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
    
    def task_single_crawl(self, payload: TaskWebCrawlerPayload):
        lg = AppCtxLogger()
        lg.event_name("TaskSingleCraw")
        lg.field("payload.json_result_format", payload.json_result_format)
        lg.field("payload.clue", payload.clue)
        lg.field("payload.current_transaction_attempt", payload.current_transaction_attempt)
        lg.field("payload.max_retry", payload.max_retry)

        try:
            error_last = None
            dic_json_result = None
            print("max retry ==>>> ", payload.max_retry)

            for attempt in range(1, payload.max_retry + 1):
                try:
                    print("attempt ==>>> ", attempt)
                    cleaned_html = self.__start_stealth_craw_with_html_output(payload.target_url, 1)
                    print(cleaned_html)

                    self.extract_markdown_to_json_agent.set_prompt(type="transform")
                    raw_json = self.extract_markdown_to_json_agent.exec_transform(TransformToJSONParam(
                        source=cleaned_html,
                        source_type="html",
                        json_result_format=payload.json_result_format,
                        clue=payload.clue,
                    ))

                    raw_json = raw_json.replace("`", "")
                    raw_json = raw_json.replace("json", "")

                    print("raw result ==>>> ", raw_json)
                    dic_json_result = json.loads(raw_json)
                    print("dic json result ===<< ", dic_json_result)
                    error_last = None
                    break  # break out of retry loop if successful

                except Exception as e:
                    print("errr ==>>>> ", e)
                    error_last = e
                    time.sleep(5)  # Wait a bit before retry

        except Exception as e:
            lg.error("error crawl or decode response to json reach max retry", error=e)
        finally:
            webhook_status = "malformed"

            if error_last is not None:
                webhook_status = "failed"

            if dic_json_result is not None:
                webhook_status = "success"

            print("call webhook with status=", webhook_status)

    def __start_stealth_craw_with_html_output(self, target_url: str, max_window_scroll: int = 2) -> str:
        display = Display(visible=0, size=(1920, 1080))
        uc_chrome = None
        try:
            display.start()

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

            uc_chrome = uc.Chrome(options=options, headless=False)
            uc_chrome.get(target_url)

            WebDriverWait(uc_chrome, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(5)
            uc_chrome.implicitly_wait(15)

            for _ in range(max_window_scroll):
                uc_chrome.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            html = uc_chrome.page_source

            soup = BeautifulSoup(html, "html.parser")

            for tag in soup(["script", "style", "img", "meta", "link", "noscript"]):
                tag.decompose()

            for a in soup.find_all("a", href=True):
                a.unwrap()

            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            for tag in soup.find_all():
                if not tag.get_text(strip=True):
                    tag.decompose()

            return soup.prettify()
        finally:
            if uc_chrome:
                uc_chrome.quit()
            display.stop()


    
