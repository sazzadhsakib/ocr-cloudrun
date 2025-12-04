import time
import json
from fastapi import UploadFile, HTTPException
from google.cloud import vision
from src.utils.file_utils import validate_file
from src.services.metadata import extract_metadata
from src.services.confidence import compute_confidence
from src.services.cache_service import get_cache, set_cache
from src.services.preprocess import preprocess_image
from src.services.text_utils import clean_text
from src.services.logger import logger
from src.models.response_models import SingleOCRResponse, OCRResult, BatchOCRResponse

client = vision.ImageAnnotatorClient()

async def process_single_image(image: UploadFile) -> SingleOCRResponse:
    logger.info(json.dumps({"event": "request_received", "filename": image.filename}))
    contents = await validate_file(image)

    cached = get_cache(contents)
    if cached:
        logger.info(json.dumps({"event": "cache_hit", "filename": image.filename}))
        return SingleOCRResponse(**cached)

    processed_bytes, original_format = preprocess_image(contents)
    logger.info(json.dumps({"event": "preprocessing_done", "filename": image.filename, "original_format": original_format}))

    start_time = time.time()
    vision_image = vision.Image(content=processed_bytes)
    response = client.document_text_detection(image=vision_image)

    if response.error.message:
        logger.error(json.dumps({"event": "vision_api_error", "error": response.error.message}))
        raise HTTPException(status_code=500, detail=response.error.message)

    text = response.text_annotations[0].description if response.text_annotations else ""
    text = clean_text(text)

    confidence = compute_confidence(response.full_text_annotation) or 0.0
    metadata = extract_metadata(processed_bytes, original_format)

    result_dict = {
        "success": bool(text),
        "text": text,
        "confidence": confidence,
        "metadata": metadata,
        "processing_time_ms": int((time.time() - start_time) * 1000)
    }

    set_cache(contents, result_dict)
    logger.info(json.dumps({"event": "response_ready", "filename": image.filename, "result": result_dict}))

    return SingleOCRResponse(**result_dict)

async def process_batch_images(images: list[UploadFile]) -> BatchOCRResponse:
    results = []
    total_start = time.time()

    for img in images:
        single_result = await process_single_image(img)
        reordered_result = OCRResult(
            filename=img.filename,
            success=single_result.success,
            text=single_result.text,
            confidence=single_result.confidence,
            metadata=single_result.metadata,
            processing_time_ms=single_result.processing_time_ms
        )
        results.append(reordered_result)

    total_processing_time = int((time.time() - total_start) * 1000)
    batch_response = BatchOCRResponse(
        success=True,
        total_images=len(images),
        total_processing_time_ms=total_processing_time,
        results=results
    )

    logger.info(json.dumps({
        "event": "batch_response_ready",
        "total_images": len(images),
        "total_processing_time_ms": total_processing_time
    }))

    return batch_response
