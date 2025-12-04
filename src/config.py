from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    MAX_GIF_SIZE: int = 10 * 1024 * 1024
    MAX_GIF_FRAMES: int = 50
    MAX_BATCH_FILES: int = 10

    CACHE_TTL: int = 7200
    CACHE_MAXSIZE: int = 500

    LOG_FILE: str = "logs/ocr_service.log"
    CONTRAST_ENHANCE_FACTOR: float = 1.2
    JPEG_QUALITY: int = 90

    # Rate Limiting Settings
    RATE_LIMIT_SINGLE: str = "100/minute"
    RATE_LIMIT_BATCH: str = "20/minute"
    RATE_LIMIT_GLOBAL: str = "200/minute"

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
