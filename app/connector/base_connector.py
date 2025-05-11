from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.runnables import RunnableSequence

from app.transform import dict_to_class

class BaseConnector:
    def __init__(self) -> None:
        self.base_url: str = None
        self.timeout_second: int = 30

    def _response_to_class(self, cls, data):
        return dict_to_class(cls, data)
    
    def set_base_url(self, base_url: str):
        self.base_url = base_url
    
    def set_timeout_second(self, timeout_second: int):
        self.timeout_second = timeout_second
