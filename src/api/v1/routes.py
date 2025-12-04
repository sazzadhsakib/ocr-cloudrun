from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Request
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.services.ocr_service import process_single_image, process_batch_images
from src.models.response_models import SingleOCRResponse, BatchOCRResponse
from src.services.cache_service import get_cache
from src.config import settings

router = APIRouter()

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)


@router.post("/extract-text", response_model=SingleOCRResponse)
@limiter.limit(settings.RATE_LIMIT_SINGLE)
async def extract_text(
    request: Request, response: Response, image: UploadFile = File(...)
):
    """
    Process a single image and return OCR result.
    Adds cache headers if available.
    Rate limited to 100 requests per minute per IP.
    """
    try:
        contents = await image.read()
        cached = get_cache(contents)

        if cached:
            response.headers["X-Cache-Status"] = "cached"
            response.headers["X-Cache-Timestamp"] = cached.get("_cached_at", "")
        else:
            response.headers["X-Cache-Status"] = "not-cached"

        return await process_single_image(
            image, preloaded_bytes=contents, preloaded_mimetype=image.content_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-extract", response_model=BatchOCRResponse)
@limiter.limit(settings.RATE_LIMIT_BATCH)
async def batch_extract(
    request: Request, response: Response, images: List[UploadFile] = File(...)
):
    """
    Process multiple images in batch.
    Returns 207 Multi-Status if some images fail.
    Adds consolidated cache headers.
    Rate limited to 20 requests per minute per IP.
    """
    try:
        timestamps = []
        for img in images:
            contents = await img.read()
            cached = get_cache(contents)
            if cached:
                timestamps.append(cached.get("_cached_at", ""))
            await img.seek(0)  # rewind file for processing

        if timestamps and len(timestamps) == len(images):
            response.headers["X-Cache-Status"] = "all-cached"
        elif timestamps:
            response.headers["X-Cache-Status"] = "mixed"
        else:
            response.headers["X-Cache-Status"] = "not-cached"

        response.headers["X-Cache-Timestamps"] = ",".join(timestamps)

        batch_response, status_code = await process_batch_images(images)
        response.status_code = status_code
        return batch_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
@limiter.exempt  # Exempt health checks from rate limiting
async def health_check():
    """Health check endpoint - not rate limited"""
    return {"status": "healthy", "service": "ocr-api"}
