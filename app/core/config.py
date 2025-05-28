import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(override=True)

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

    # TELEGRAM
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")

    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY")

    DB_NAME: str  = os.getenv("DB_NAME", "db_name")
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "yoursecurepassword")

    class Config:
        env_file = ".env"
        case_sensitive = True

def get_config():
    return Config()

config = Config()
