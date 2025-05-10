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
            "- 🔐 Potential security risks (e.g., exposed secrets, unsafe logic)\n"
            "- 🔑 **Sensitive Data Check**: Ensure no sensitive data such as passwords, email addresses, phone numbers, or other PII (Personally Identifiable Information) is being logged, stored, or handled insecurely. "
            "Make sure any sensitive information is encrypted before storing or logging.\n\n"
            "**this is considered highly secure and should not be flagged**. "
            "- ♻️ **Redundant Code Check**: Check if there are any sections of code that are redundant, repeated, or could be simplified without losing functionality. Redundant code should be refactored to improve maintainability.\n\n"
            "❗ Do not ask any follow-up questions at the end.\n\n"
            "🎯 Finally, provide a score (0–100) based on the following criteria:\n"
            "- **Simplicity of Code**: Are the changes simple and clear, without redundant complexity? (Score 0–40)\n"
            "- **Security**: Is the code secure with no major security risks? (Score 0–30)\n"
            "- **Sensitive Data Logging**: Are sensitive data (passwords, emails, PII) logged inappropriately? "
            "(Score 0–30, major penalty for exposed sensitive data)"
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
            self.analysis_prompt = (
                analysis_goal
                + "\n\n❗ Do not ask any follow-up questions at the end."
                + "\n\n🎯 Finally, provide a score (0–100) for the overall quality of the code changes."
            )

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
