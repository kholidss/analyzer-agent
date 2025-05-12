from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.runnables import RunnableSequence
from dataclasses import dataclass

from app.agent.base_agent import BaseAgent

@dataclass
class SolvingExamParam:
    question: str

class SolvingExam(BaseAgent):
    def __init__(
        self,
        model_name: str = "gemma:1b",
        mode: str = "local",
        base_url: str = None,
        api_key: str = None
    ) -> None:
        super().__init__(model_name=model_name, mode=mode, base_url=base_url, api_key=api_key)
        self.analysis_prompt: str = (
        "Bacalah soal berikut dan pilih atau isi jawaban yang paling tepat. Jika soal melibatkan operasi perhitungan atau matematika, selesaikan sesuai dengan aturan matematika yang berlaku, dan gunakan format diketahui, ditanya, dan lansung kerjakan dengan cara yang praktis tanpa ada kata-kata\n\n"
        "Jawaban harus seolah - olah bukan jawaban dari AI.\n\n"
        "Diakhir sesi, kamu jangan tanyakan kembali sebuah pertanyaan\n\n"
        )

    def exec_answer(self, param: SolvingExamParam) -> str:
        chain: RunnableSequence = self.prompt | self.llm
        result = chain.invoke({
            "question": param.question,
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

        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "Anda adalah seorang guru atau dosen senior yang memberikan penjelasan dan jawaban yang jelas untuk soal-soal yang diberikan. Berikan langkah-langkah penyelesaian secara rinci."
            ),
            HumanMessagePromptTemplate.from_template("""
                📚 Soal:

                {question}

                {analysis_prompt}
            """)
        ])

