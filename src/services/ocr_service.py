import time
from fastapi import UploadFile, HTTPException
from google.cloud import vision
from src.utils.file_utils import validate_file
from src.services.metadata import extract_metadata
from src.services.confidence import compute_confidence
from src.services.cache_service import get_cache, set_cache
from src.services.preprocess import preprocess_image

client = vision.ImageAnnotatorClient()


async def process_single_image(image: UploadFile):
    contents = await validate_file(image)
    cached = get_cache(contents)
    if cached:
        return cached

    # Preprocess image and get original format
    processed_bytes, original_format = preprocess_image(contents)

    start = time.time()
    vision_image = vision.Image(content=processed_bytes)
    response = client.document_text_detection(image=vision_image)

    if response.error.message:
        raise HTTPException(status_code=500, detail=response.error.message)

    annotations = response.text_annotations
    extracted_text = annotations[0].description if annotations else ""
    confidence = compute_confidence(response.full_text_annotation)
    metadata = extract_metadata(processed_bytes, original_format)

    result = {
        "success": bool(extracted_text),
        "text": extracted_text,
        "confidence": confidence,
        "metadata": metadata,
        "processing_time_ms": int((time.time() - start) * 1000),
    }

    set_cache(contents, result)
    return result


async def process_batch_images(images: list[UploadFile]):
    """
    Process multiple images in a batch and return structured response
    with filename as the first key.
    """
    results = []
    total_start = time.time()

    for img in images:
        single_result = await process_single_image(img)

        # Reorder keys: filename first
        reordered_result = {
            "filename": img.filename,
            "success": single_result["success"],
            "text": single_result["text"],
            "confidence": single_result["confidence"],
            "metadata": single_result["metadata"],
            "processing_time_ms": single_result["processing_time_ms"],
        }

        results.append(reordered_result)

    total_processing_time = int((time.time() - total_start) * 1000)

    return {
        "success": True,
        "total_images": len(images),
        "total_processing_time_ms": total_processing_time,
        "results": results,
    }
