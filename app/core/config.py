import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Config(BaseSettings):
    # APP
    APP_NAME: str = os.getenv("APP_NAME", "analyzer-agent")
    APP_ENV: str = os.getenv("APP_ENV", "local")

    # LLM
    LLM_GENERAL_MODEL: str = os.getenv("LLM_GENERAL_MODEL", "gemma3:1b")
    LLM_MODE: str = os.getenv("LLM_MODE", "local")
    LLM_API_BASE_URL: str = os.getenv("LLM_API_BASE_URL", "")
    LLM_API_API_KEY: str = os.getenv("LLM_API_API_KEY", "")

    # GITHUB
    GITHUB_API_BASE_URL: str = os.getenv("GITHUB_API_BASE_URL", "")

    class Config:
        env_file = ".env"
        case_sensitive = True

def get_config():
    return Config()

config = Config()
