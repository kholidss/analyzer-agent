from dataclasses import dataclass

from app.agent.agent__code_analyzer import *
from app.agent.agent__transform_to_json import TransformToJSON, TransformToJSONParam
from app.logger import AppCtxLogger

from app.connector.connector__github_api import CommentOnPRPayload, GithubAPIConnector
import json


@dataclass
class TaskTransformToJSONPayload:
    source: str
    source_type: str
    json_result: str
    clue: str


class TransformToJSONWorker():
    def __init__(self, extract_markdown_to_json_agent: TransformToJSON):
        self.extract_markdown_to_json_agent = extract_markdown_to_json_agent

    def task_transform_to_json(self, payload: TaskTransformToJSONPayload):
        lg = AppCtxLogger()
        lg.event_name("TaskMarkdownToJSON")
        lg.field("payload.json_result", payload.json_result)
        lg.field("payload.clue", payload.clue)

        self.extract_markdown_to_json_agent.set_prompt(type="transform")
        json_result = self.extract_markdown_to_json_agent.exec_transform(TransformToJSONParam(
            source=payload.source,
            source_type=payload.source_type,
            json_result=payload.json_result,
            clue=payload.clue,
        ))

        clean_result = json_result.replace("`", "")
        clean_result = clean_result.replace("json", "")

        print("before result ==>>> ", clean_result)
        data_dict = json.loads(clean_result)

        # print(data_dict['pricelist'][0])  

        print("result ===<< ", data_dict)

    
