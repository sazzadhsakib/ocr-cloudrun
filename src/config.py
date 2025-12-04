from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    MAX_GIF_SIZE: int = 3 * 1024 * 1024
    MAX_GIF_FRAMES: int = 50

    CACHE_TTL: int = 3600
    CACHE_MAXSIZE: int = 200

    LOG_FILE: str = "logs/ocr_service.log"
    CONTRAST_ENHANCE_FACTOR: float = 1.2
    JPEG_QUALITY: int = 90

    # Rate Limiting Settings
    RATE_LIMIT_SINGLE: str = "100/minute"  # 100 requests per minute for single image
    RATE_LIMIT_BATCH: str = "20/minute"  # 20 requests per minute for batch
    RATE_LIMIT_GLOBAL: str = "200/minute"  # Global limit per IP

    # Pydantic v2 way
    model_config = ConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
