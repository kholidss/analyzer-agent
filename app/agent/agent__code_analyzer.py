from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.runnables import RunnableSequence
from dataclasses import dataclass

from app.agent.base_agent import BaseAgent

@dataclass
class CodeAnalyzerEvaluateParam:
    pr_title: str
    pr_body: str
    pr_patch: str

class CodeAnalyzer(BaseAgent):
    def __init__(self, model_name: str = "gemma3:1b") -> None:
        super().__init__(model_name=model_name)
        self.analysis_prompt: str = (
        "Please review this Pull Request in a **simple, friendly, and helpful** tone.\n\n"
        "Keep your response concise and use bullet points with emojis.\n\n"
        "Focus your review on the following areas:\n"
        "- ✅ **Summary**: What’s being changed (brief and clear overview).\n"
        "- 👍 **What’s Good**: Improvements, cleanups, or enhancements.\n"
        "- ⚠️ **Concerns**: Potential issues, confusing logic, or edge cases.\n"
        "- 🔐 **Security Review**: Look for unsafe patterns (e.g., hardcoded secrets, unsafe use of external input, missing validation).\n"
        "- 🔑 **Sensitive Data Handling**: Ensure **no PII** (passwords, emails, phone numbers) is logged or stored insecurely. Highlight any area where encryption or redaction should be applied.\n"
        "❗ Please **do not** ask follow-up questions or request clarification.\n\n"
        "🎯 End with a review **score (0–100)** based on:\n"
        "- **Code Simplicity (0–40)**: Clear, concise, and maintainable?\n"
        "- **Security (0–30)**: Any major vulnerabilities?\n"
        "- **Sensitive Data Safety (0–30)**: Any improper exposure or logging of sensitive info?\n"
        )


    def exec_evaluate(self, param: CodeAnalyzerEvaluateParam) -> str:
        chain: RunnableSequence = self.prompt | self.llm
        return chain.invoke({
            "pr_title": param.pr_title,
            "pr_body": param.pr_body,
            "pr_patch": param.pr_patch,
            "analysis_prompt": self.analysis_prompt
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
