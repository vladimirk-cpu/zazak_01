from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
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
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"
    
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./data/logs"

    # Email notifications
    MAIL_TO: str
    MAIL_FROM: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
