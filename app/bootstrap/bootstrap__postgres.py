from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.runnables import RunnableSequence
from dataclasses import dataclass

from app.agent.base_agent import BaseAgent
from app.core.config import Config
import psycopg
from psycopg import Connection 

class PersistencePostgreSQL:
    def __init__(
        self,
        cfg: Config,
    ) -> None:
        self.cfg = cfg
        self.conn: Connection = None

    async def connect(self):
        self.conn = psycopg.connect(
            dbname=self.cfg.DB_NAME,
            user=self.cfg.DB_USER,
            password=self.cfg.DB_PASSWORD,
            host=self.cfg.DB_HOST,
        )

    def conn(self) -> Connection:
        return self.conn

    def table_schema(self):
        query = """
            SELECT table_schema, table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name, ordinal_position;
        """
        schema = {}
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            # Process the rows into a structured dictionary
            for table_schema, table_name, column_name, data_type in rows:
                # Create a unique key for each table as `schema_name.table_name`
                key = f"{table_schema}.{table_name}"
                # Add columns to the schema dictionary
                schema.setdefault(key, []).append({
                    "column_name": column_name,
                    "data_type": data_type
                })

        return schema


    
    async def close(self):
        self.conn.close()
