from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.runnables import RunnableSequence
from dataclasses import dataclass

from app.agent.base_agent import BaseAgent

@dataclass
class TransformToJSONParam:
    source: str
    source_type: str
    json_result_format: str
    clue: str = ""

class TransformToJSON(BaseAgent):
    def __init__(
        self,
        model_name: str = "gemma:1b",
        mode: str = "local",
        base_url: str = None,
        api_key: str = None
    ) -> None:
        super().__init__(model_name=model_name, mode=mode, base_url=base_url, api_key=api_key)
        self.analysis_prompt: str = None

    def exec_transform(self, param: TransformToJSONParam) -> str:
        chain: RunnableSequence = self.prompt | self.llm
        analysis_prompt = (
            f"Convert the following {param.source_type} into a valid JSON format. Respond ONLY with the resulting JSON. Do not include any explanations or additional text.\n\n"
        )
        result = chain.invoke({
            "analysis_prompt": analysis_prompt,
            "source": param.source,
            "source_type": param.source_type,
            "json_result_format": param.json_result_format,
            "clue": param.clue,
        })

        if hasattr(result, "content"):
            return result.content

        if isinstance(result, dict) and "content" in result:
            return result["content"]

        return result

    def set_prompt(self, type: str = "transform", analysis_goal: str = ""):
        if type == "train":
            self.prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate.from_template("{train_prompt}")
            ])
            return

        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "You are an expert at converting source into structured JSON."
            ),
            HumanMessagePromptTemplate.from_template("""
                {analysis_prompt}

                "{source_type} Input":

                {source}

                "Expected JSON Output Format:

                {json_result_format}

                "Clue(optional)":

                {clue}
                """)
            ])
