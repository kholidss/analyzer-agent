from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.runnables import RunnableSequence
from dataclasses import dataclass

from app.agent.base_agent import BaseAgent

@dataclass
class CVEvaluatorParam:
    cv_text: str

class CVEvaluator(BaseAgent):
    def __init__(
        self,
        model_name: str = "gemma:1b",
        mode: str = "local",
        base_url: str = None,
        api_key: str = None
    ) -> None:
        super().__init__(model_name=model_name, mode=mode, base_url=base_url, api_key=api_key)
        self.analysis_prompt: str = (
        """Please response with the following format "YES" or "NO" based on the Requirement Points and give the short brief reason"""
        )

    def exec_evaluate(self, param: CVEvaluatorParam) -> str:
        chain: RunnableSequence = self.prompt | self.llm
        result = chain.invoke({
            "cv_text": param.cv_text,
            "analysis_prompt": self.analysis_prompt
        })

        if hasattr(result, "content"):
            return result.content

        if isinstance(result, dict) and "content" in result:
            return result["content"]
        
        return result

    def set_prompt(self, type: str = "answer", analysis_goal: str = ""):
        if type == "train":
            self.prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate.from_template("{train_prompt}")
            ])
            return
        
        if analysis_goal == "score":
            self.analysis_prompt = """Please response with a score using the following format:"TOTAL SCORE: (based on the total score for the 'Requirements')" and give the short brief reason"""

        self.prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(
                    "You are a CV evaluation assistant."),
                HumanMessagePromptTemplate.from_template("""
                   The following is a candidate's CV:

                    {cv_text}

                    Please evaluate whether this candidate is suitable or relate for the Software Engineer, Backend Engineer job position.
                    "Requirements":
                    1. Candidate must have a minimum of 2 years of total working experience or more. (if fulfilled, then the score is 40)
                    2. Must have included all of this skills (Golang, Node JS). (if fulfilled, then the score is 40)
                    3. Must have attended education in Indonesia. (if fulfilled, then the score is 20)
                                                         
                    Minimum passed score is = 80

                    {analysis_prompt}
                    """)
        ])

