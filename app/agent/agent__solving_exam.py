from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.runnables import RunnableSequence
from dataclasses import dataclass

from app.agent.base_agent import BaseAgent

@dataclass
class SolvingExamParam:
    question: str

class SolvingExam(BaseAgent):
    def __init__(self, model_name: str = "gemma3:1b") -> None:
        super().__init__(model_name=model_name)
        self.analysis_prompt: str = (
        "Bacalah soal berikut dan pilih atau isi jawaban yang paling tepat. Jika soal melibatkan operasi perhitungan atau matematika, selesaikan sesuai dengan aturan matematika yang berlaku. Jawabannya harus disertai langkah-langkah yang jelas.\n\n"
        "Jika soal berupa pilihan ganda, pilih salah satu jawaban dengan menjelaskan alasan dari pemilihan tersebut.\n\n"
        "Jawaban harus seolah - olah bukan jawaban dari AI.\n\n"
        )

    def exec_answer(self, param: SolvingExamParam) -> str:
        chain: RunnableSequence = self.prompt | self.llm
        return chain.invoke({
            "question": param.question,
            "analysis_prompt": self.analysis_prompt
        })

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

