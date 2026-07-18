from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str
    CHAT_ID: str

    TELEGRAM_PROXY_ENABLED: bool = False
    TELEGRAM_PROXY_TYPE: str = "socks5"

    TELEGRAM_PROXY_HOST: str = ""
    TELEGRAM_PROXY_PORT: int = 1080

    TELEGRAM_PROXY_USER: str = ""
    TELEGRAM_PROXY_PASSWORD: str = ""

    TELEGRAM_TIMEOUT: int = 15
    TELEGRAM_SILENT: bool = False
    TELEGRAM_MAX_RETRIES: int = 3
    TELEGRAM_RETRY_AFTER_MAX: int = 60

    # API
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    QUEUE_MAX_SIZE: int = 1000
    MESSAGE_MAX_LENGTH: int = 3900

    # Файлы
    TOKENS_FILE: str = "tokens.conf"

    # Логи
    LOG_DIR: str = "logs"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
