from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
import json
from src.services.logger import logger


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom rate limit exceeded handler with logging"""

    # Log the rate limit violation
    logger.warning(
        json.dumps(
            {
                "event": "rate_limit_exceeded",
                "ip": request.client.host,
                "path": request.url.path,
                "method": request.method,
                "limit": str(exc.detail),
            }
        )
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail),
        },
        headers={"Retry-After": "60"},  # Suggest retry after 60 seconds
    )
