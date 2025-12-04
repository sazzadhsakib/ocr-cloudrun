import time
import json
import asyncio
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from google.cloud import vision
from src.utils.file_utils import _validate_image_bytes, validate_file
from src.services.metadata import extract_metadata
from src.services.confidence import compute_confidence
from src.services.cache_service import get_cache, set_cache
from src.services.preprocess import preprocess_image
from src.services.logger import logger
from src.models.response_models import SingleOCRResponse, OCRResult, BatchOCRResponse

client = vision.ImageAnnotatorClient()


async def _call_document_text_detection(processed_bytes: bytes):
    """Async wrapper for blocking Vision API call."""
    loop = asyncio.get_running_loop()
    vision_image = vision.Image(content=processed_bytes)
    return await loop.run_in_executor(None, client.document_text_detection, vision_image)


def _build_result_dict_from_response(
    response,
    processed_bytes: bytes,
    original_format: str,
    mimetype: str,
    start_time: float,
):
    """Build OCR result dict from Vision response."""
    text = response.text_annotations[0].description if response.text_annotations else ""
    confidence = compute_confidence(response.full_text_annotation) or 0.0
    metadata = extract_metadata(processed_bytes, original_format, mimetype)
    result = {
        "success": bool(text),
        "text": text,
        "confidence": confidence,
        "metadata": metadata,
        "processing_time_ms": int((time.time() - start_time) * 1000),
        "error": None
    }
    # Set error if OCR produced no text
    if not text:
        result["error"] = "No text detected in image."
    return result


async def _process_single_safe(filename: str, contents: bytes, mimetype: str) -> dict:
    """Safe single-image processing; always returns dict with error info if fails."""
    start_time = time.time()
    try:
        _validate_image_bytes(contents, mimetype)

        cached = get_cache(contents)
        if cached:
            logger.info(json.dumps({"event": "cache_hit", "filename": filename}))
            return {**cached}

        processed_bytes, original_format = preprocess_image(contents)
        logger.info(json.dumps({"event": "preprocessing_done", "filename": filename, "original_format": original_format}))

        response = await _call_document_text_detection(processed_bytes)
        if getattr(response, "error", None) and response.error.message:
            raise Exception(response.error.message)

        result = _build_result_dict_from_response(response, processed_bytes, original_format, mimetype, start_time)
        set_cache(contents, result)
        logger.info(json.dumps({"event": "response_ready", "filename": filename, "result": result}))
        return result

    except HTTPException as he:
        logger.warning(json.dumps({"event": "validation_error", "filename": filename, "error": he.detail}))
        return {"success": False, "text": "", "confidence": 0.0, "metadata": None, "processing_time_ms": 0, "error": str(he.detail)}

    except Exception as e:
        logger.error(json.dumps({"event": "processing_error", "filename": filename, "error": str(e)}))
        return {"success": False, "text": "", "confidence": 0.0, "metadata": None, "processing_time_ms": 0, "error": str(e)}


async def process_single_image(
    image: UploadFile,
    preloaded_bytes: Optional[bytes] = None,
    preloaded_mimetype: Optional[str] = None,
) -> SingleOCRResponse:
    """Single image OCR endpoint processor; raises HTTPException on failure."""
    logger.info(json.dumps({"event": "request_received", "filename": image.filename}))
    contents = preloaded_bytes or await validate_file(image)
    mimetype = preloaded_mimetype or image.content_type

    result = await _process_single_safe(image.filename, contents, mimetype)
    if not result.get("success", False):
        raise HTTPException(status_code=500, detail=result.get("error", "OCR failed"))
    return SingleOCRResponse(**result)


async def process_batch_images(
    images: list[UploadFile],
) -> Tuple[BatchOCRResponse, int]:
    """Process multiple images sequentially. Returns batch response and status code (207 if partial failure)."""
    results = []
    total_start = time.time()
    any_failure = False

    for img in images:
        contents = await img.read()
        mimetype = img.content_type
        await img.seek(0)  # rewind so UploadFile can be reused
        single_result = await _process_single_safe(img.filename, contents, mimetype)

        ocr_result = OCRResult(
            filename=img.filename,
            success=single_result.get("success", False),
            text=single_result.get("text", ""),
            confidence=single_result.get("confidence", 0.0),
            metadata=single_result.get("metadata"),
            processing_time_ms=single_result.get("processing_time_ms", 0),
            error=single_result.get("error"),  # now always populated
        )

        if not ocr_result.success:
            any_failure = True
        results.append(ocr_result)

    total_processing_time = int((time.time() - total_start) * 1000)
    batch_response = BatchOCRResponse(
        success=not any_failure,
        total_images=len(images),
        total_processing_time_ms=total_processing_time,
        results=results,
    )
    status_code = 200 if not any_failure else 207

    logger.info(json.dumps({
        "event": "batch_response_ready",
        "total_images": len(images),
        "total_processing_time_ms": total_processing_time,
        "any_failure": any_failure,
    }))

    return batch_response, status_code
