from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI

class BaseAgent:
    def __init__(self, model_name: str, mode: str = "local", base_url: str = None, api_key: str = None):
        print(f"🚀 Initializing CodeAnalyzer with model: {model_name}")
        if mode == "api":
            if not base_url and not api_key:
                raise ValueError(f"Mode '{mode}' must be provided with 'base_url' and 'api_key'.")
            self.llm = ChatOpenAI(
                model=model_name,
                openai_api_key=api_key,
                openai_api_base=base_url,
                streaming=False
            )
        elif mode == "local":
            self.llm = OllamaLLM(model=model_name, temperature=0.3)
        else:
            raise ValueError(f"Mode '{mode}' is not recognized. Use 'api' or 'local'.")
        
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