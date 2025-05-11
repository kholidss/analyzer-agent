from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.runnables import RunnableSequence

class BaseAgent:
    def __init__(self, model_name: str = "gemma3:1b") -> None:
        self.llm: OllamaLLM = OllamaLLM(model=model_name)
        self.prompt: ChatPromptTemplate = None
        self.analysis_prompt: str = None
        self.invoke_parameter: dict = None
        self.train_parameter: dict = None

    def set_llm(self, llm: str):
        self.llm = llm

    def set_dict_invoke_parameter(self, param: dict):
        self.invoke_parameter = param
    
    def set_dict_train_parameter(self, param: dict):
        self.train_parameter = param

    def set_prompt(self, type: str = "train", analysis_goal: str = None):
        if type == "train":
            self.prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate.from_template("{train_prompt}")
        ])

    def common_exec(self, new_parameter: dict = None) -> str:
        param = self.invoke_parameter
        if new_parameter is not None:
            param = new_parameter
        chain: RunnableSequence = self.prompt | self.llm
        return chain.invoke(param)

    def common_train(self, new_parameter: dict = None) -> str:
        param = self.train_parameter
        if new_parameter is not None:
            param = new_parameter
        chain: RunnableSequence = self.prompt | self.llm
        return chain.invoke(param)