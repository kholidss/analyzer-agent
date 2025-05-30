from langchain_community.utilities import SerpAPIWrapper
from langchain_community.tools import Tool
from langgraph.graph import StateGraph, END

from typing import TypedDict, Literal, Optional
from app.agent.base_agent import BaseAgent
import re
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from tabulate import tabulate
from app.bootstrap.bootstrap__postgres import BootstrapPostgres

class TelegramAssistant(BaseAgent):
    class State(TypedDict):
        input: str
        intent: Optional[Literal["search", "health_analysis", "search_postgresql_data", "unknown"]]
        output: Optional[str]

    def __init__(
        self,
        model_name: str = "gemma:1b",
        mode: str = "local",
        base_url: str = None,
        api_key: str = None,
        serpapi_api_key: str = None,
        db: BootstrapPostgres= None,
    ) -> None:
        super().__init__(model_name=model_name, mode=mode, base_url=base_url, api_key=api_key)

        self.db = db.conn

        self.schema_tables = db.table_schema()
        
        self.analysis_prompt: str = (
            "Bacalah soal berikut dan pilih atau isi jawaban yang paling tepat. Jika soal melibatkan operasi perhitungan atau matematika, selesaikan sesuai dengan aturan matematika yang berlaku, dan gunakan format diketahui, ditanya, dan lansung kerjakan dengan cara yang praktis tanpa ada kata-kata\n\n"
            "Jawaban harus seolah - olah bukan jawaban dari AI.\n\n"
            "Diakhir sesi, kamu jangan tanyakan kembali sebuah pertanyaan\n\n"
        )

        self.serpapi_api_key = serpapi_api_key

        self.search_tool = Tool.from_function(
            func=lambda q: SerpAPIWrapper(serpapi_api_key=serpapi_api_key).run(q, return_raw=True),
            name="Google Search",
            description="Gunakan Google Search untuk mencari informasi."
        )

        self.tools = {
            "search": self.search_tool.run,
            "health_analysis": lambda x: "Berikut analisa kesehatan berdasarkan masukan Anda: " + x + "\n\n",
            "search_postgresql_data": lambda x: "Berikut hasil data berdasarkan masukan Anda: " + x + "\n\n",
        }

        # Build LangGraph workflow
        self.workflow = StateGraph(self.State)
        self.workflow.add_node("detect_intent", self.detect_intent)
        self.workflow.add_node("search", self.handle_search)
        self.workflow.add_node("health_analysis", self.handle_health)
        self.workflow.add_node("search_postgresql_data", self.handle_search_postgresql)
        self.workflow.add_node("unknown", self.handle_unknown)

        self.workflow.set_entry_point("detect_intent")
        self.workflow.add_conditional_edges("detect_intent", self.route_intent, {
            "search": "search",
            "health_analysis": "health_analysis",
            "search_postgresql_data": "search_postgresql_data",
            "unknown": "unknown",
        })
        self.workflow.add_edge("search", END)
        self.workflow.add_edge("health_analysis", END)
        self.workflow.add_edge("search_postgresql_data", END)
        self.workflow.add_edge("unknown", END)

        self.graph_executor = self.workflow.compile()

    def detect_intent(self, state: "TelegramAssistant.State") -> "TelegramAssistant.State":
        prompt = (
            "Determine the user's intent based on the following input.\n"
            "Available intents:\n"
            "- search → if they want to search for research or information\n"
            "- health_analysis → if they want health analysis\n"
            "- search_postgresql_data → if they want to search data in a postgresql database\n"
            "- unknown → if it doesn't match any of the above\n"
            f"User input: {state['input']}\n"
            "Your response must be in this format:\n"
            "```answer\n"
            "ONE OF: search, health_analysis, search_postgresql_data, unknown\n"
            "```"
        )
        response = self.llm.invoke(prompt)
        intent_text = response.content.strip().lower()

        print("intent_text ==>>> ", intent_text)
        
        # Extract intent from the ```answer ... ``` block
        match = re.search(r'```answer\s*(.*?)\s*```', intent_text, re.DOTALL)
        if match:
            extracted_text = match.group(1).strip().lower()
            
            # Check for each intent specifically, with longer matches first to avoid partial matches
            if "search_postgresql_data" in extracted_text:
                intent = "search_postgresql_data"
            elif "health_analysis" in extracted_text:
                intent = "health_analysis"
            elif "search" in extracted_text:
                intent = "search"
            elif "unknown" in extracted_text:
                intent = "unknown"
            else:
                intent = "unknown"  # Default if no valid intent found
        else:
            # Fallback if no answer block is found
            if "search_postgresql_data" in intent_text:
                intent = "search_postgresql_data"
            elif "health_analysis" in intent_text:
                intent = "health_analysis"
            elif "search" in intent_text:
                intent = "search"
            elif "unknown" in intent_text:
                intent = "unknown"
            else:
                intent = "unknown"
        
        print("intent ===>>> ", intent)
        return {**state, "intent": intent}



    def route_intent(self, state: "TelegramAssistant.State"):
        return state["intent"]

    def handle_search(self, state: "TelegramAssistant.State") -> "TelegramAssistant.State":
        query = state["input"]
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.serpapi_api_key
        }
        
        search = GoogleSearch(params)
        raw_result = search.get_dict()
        
        print("raw_result ==>>>", raw_result)
        
        urls = []
        if "organic_results" in raw_result:
            for item in raw_result["organic_results"]:
                link = item.get("link")
                if link:
                    urls.append(link)
        
        print("urls ==>>>", urls)
        
        if not urls:
            return {**state, "output": "Maaf, tidak ditemukan URL yang bisa diambil dari hasil pencarian."}
        
        page_content = self.fetch_page_content(urls[0])
        print("content ==<<<<", page_content)
        
        summarization_prompt = (
            "Berikut adalah isi halaman web hasil pencarian:\n"
            f"{page_content}\n\n"
            "Buatlah ringkasan singkat dalam bahasa Indonesia yang mudah dimengerti."
        )
        
        summary = self.llm.invoke(summarization_prompt).content.strip()
        
        return {**state, "output": clean_content_from_markdown(summary)}


    def handle_health(self, state: "TelegramAssistant.State") -> "TelegramAssistant.State":
        input_text = state["input"]
        result = self.tools["health_analysis"](input_text)
        return {**state, "output": result}
    
    def handle_search_postgresql(self, state: "TelegramAssistant.State") -> "TelegramAssistant.State":
        summarization_prompt = (
            "Berikut adalah skema tabel dan kolom PostgreSQL saat ini:\n"
            f"{self.schema_tables}\n\n"
            "Berikut adalah data atau informasi yang ingin dicari:\n"
            f"{state['input']}\n\n"
            "Tolong berikan query SQL yang sesuai untuk pencarian tersebut. "
            "Hanya balas dengan query SQL tanpa penjelasan tambahan."
        )
        
        raw_query = self.llm.invoke(summarization_prompt).content.strip()
        print("raw_query ==>>> ", raw_query)
        clean_query = clean_sql_markdown(raw_query)
        print("clean_query ==>>> ", clean_query)

        result = self.execute_sql(clean_query)
        result = self.tools["search_postgresql_data"](result)
        print("rr ==>>> ", result)
        
        return {**state, "output": result}
    
    def execute_sql(self, sql_query):
        try:
            with self.db.cursor() as cursor:
                cursor.execute(sql_query)
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                # Fetch all rows
                results = cursor.fetchall()

            # Format the output as a string
            lines = [", ".join(columns)]  # Add the column names as the header
            for row in results:
                # Convert each row to a comma-separated string
                lines.append(", ".join(str(cell) for cell in row))

            return "\n".join(lines)

        except Exception as e:
            # Rollback the transaction to reset the state
            self.db.rollback()
            return f"Error executing SQL query: {e}"


    def handle_unknown(self, state: "TelegramAssistant.State") -> "TelegramAssistant.State":
        return {**state, "output": "Perintah tidak ditemukan."}

    def handle_command(self, command: str) -> str:
        result = self.graph_executor.invoke({"input": command})
        return result["output"]
    
    def fetch_page_content(self, url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)" 
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            html = response.text

            soup = BeautifulSoup(html, "html.parser")

            texts = soup.stripped_strings
            content = " ".join(texts)
            return content

        except Exception as e:
            return f"Error fetching page content: {e}"
        
    def extract_urls(self, search_results):
        urls = [item for item in search_results if isinstance(item, str) and item.startswith("https://")]
        return urls


def clean_content_from_markdown(text: str) -> str:
        text = re.sub(r'^\s*#{1,6}\s*', '', text, flags=re.MULTILINE)

        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
        text = re.sub(r'__(.*?)__', r'\1', text)      # __bold__
        text = re.sub(r'_(.*?)_', r'\1', text)        # _italic_
        text = re.sub(r'`(.*?)`', r'\1', text)        # `inline code`

        return text

def clean_sql_markdown(text: str) -> str:
    text = re.sub(r"```sql\s*", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()

def clean_routing_response(response: str) -> str:
        # Remove markdown code blocks
        response = re.sub(r'```\w*\n?', '', response)
        response = re.sub(r'```', '', response)
        
        # Remove extra whitespace and newlines
        response = response.strip()
        
        # If response contains multiple lines, take the first non-empty line
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if lines:
            response = lines[0]
        
        return response.lower()