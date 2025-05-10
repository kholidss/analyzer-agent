from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.runnables import RunnableSequence
from dataclasses import dataclass

@dataclass
class ParamCodeAnalyzerEvaluate:
    pr_title: str
    pr_body: str
    pr_patch: str

@dataclass
class ParamCodeAnalyzerTrain:
    train_prompt: str

class PRAnalyzer:
    def __init__(self, model_name: str = "gemma3:1b"):
        self.llm = OllamaLLM(model=model_name)
        self.prompt = None
        self.analysis_prompt = (
            "Give a simple and helpful review of this Pull Request.\n\n"
            "Use a casual, friendly tone. Keep it short and to the point.\n\n"
            "Respond in bullet points using emoji.\n\n"
            "Focus on:\n"
            "- ✅ What’s being changed (brief summary)\n"
            "- 👍 What looks good / improved\n"
            "- ⚠️ Any concerns or possible issues\n"
            "- 🔐 Potential security risks (e.g., exposed secrets, unsafe logic)\n\n"
            "Make it feel like a teammate giving quick, thoughtful feedback. Avoid long explanations."
        )

    def exec_evaluate(self, param: ParamCodeAnalyzerEvaluate) -> str:
        chain: RunnableSequence = self.prompt | self.llm
        return chain.invoke({
            "pr_title": param.pr_title,
            "pr_body": param.pr_body,
            "pr_patch": param.pr_patch,
            "analysis_prompt": self.analysis_prompt
        })

    def train(self, param: ParamCodeAnalyzerTrain) -> str:
        chain: RunnableSequence = self.prompt | self.llm
        return chain.invoke({
            "train_prompt": param.train_prompt
        })

    def set_prompt(self, type: str = "evaluate", analysis_goal: str = ""):
        if type == "train":
            self.prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate.from_template("{train_prompt}")
            ])
            return

        if analysis_goal:
            self.analysis_prompt = analysis_goal

        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "You are a senior developer giving quick, clear, and friendly pull request feedback. Be concise and engaging."
            ),
            HumanMessagePromptTemplate.from_template("""
                🔍 New Pull Request!

                📌 **Title**: {pr_title}

                📝 **Description**:
                {pr_body}

                🧾 **Code Changes**:
                {pr_patch}

                Time to give helpful feedback 👇

                {analysis_prompt}
            """)
        ])
