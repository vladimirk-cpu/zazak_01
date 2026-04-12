from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

class Settings(BaseSettings):
    DATA_DIR: str = "./data"
    
    ENVIRONMENT: str = "development"
    SECRET_KEY: str
    BASE_URL: str = "http://localhost:8000"

    MAX_API_URL: str = "https://api.max.ru/v1"
    MAX_BOT_TOKEN: str = ""
    MAX_CHAT_ID: str = ""

    AMOCRM_SUBDOMAIN: str = ""
    AMOCRM_CLIENT_ID: str = ""
    AMOCRM_CLIENT_SECRET: str = ""
    AMOCRM_PIPELINE_ID: int = 0
    AMOCRM_STATUS_ID: int = 0
    AMOCRM_FORM_TYPE_FIELD_ID: int = 0

    RECAPTCHA_SECRET_KEY: str = ""
    RATELIMIT_DEFAULT: str = "5/minute"
    
    # Defaults that will be overridden in __init__ if not fully specified in env
    DATABASE_URL: str = ""
    LOG_FILE_PATH: str = ""
    
    LOG_LEVEL: str = "INFO"

    # Email notifications
    MAIL_TO: str
    MAIL_FROM: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def __init__(self, **values):
        super().__init__(**values)
        
        # Ensure directories exist
        data_path = Path(self.DATA_DIR)
        data_path.mkdir(parents=True, exist_ok=True)
        (data_path / "uploads").mkdir(parents=True, exist_ok=True)
        (data_path / "logs").mkdir(parents=True, exist_ok=True)
        
        # Force construction from DATA_DIR if the values are empty or still containing the old hardcoded path
        if not self.DATABASE_URL or "./data/app.db" in self.DATABASE_URL:
            self.DATABASE_URL = f"sqlite+aiosqlite:///{data_path / 'app.db'}"
        
        if not self.LOG_FILE_PATH or self.LOG_FILE_PATH == "./data/logs":
            self.LOG_FILE_PATH = str(data_path / "logs")

settings = Settings()
