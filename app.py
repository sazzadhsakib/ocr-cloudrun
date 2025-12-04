from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.api.v1.routes import router as api_router
from src.config import settings
from src.middleware.rate_limit_middleware import rate_limit_handler

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_GLOBAL],
    storage_uri="memory://",
    headers_enabled=True,
)

# Disable Swagger / ReDoc / OpenAPI docs for production
app = FastAPI(
    title="OCR Cloud Run API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.state.limiter = limiter

# Use custom rate limit handler
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Include API router
app.include_router(api_router, prefix="/v1")


@app.get("/")
async def root():
    return {"status": "ok", "service": "OCR Cloud Run API"}
