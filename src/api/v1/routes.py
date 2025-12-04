from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from src.services.ocr_service import process_single_image, process_batch_images
from src.models.response_models import SingleOCRResponse, BatchOCRResponse

router = APIRouter()

@router.post("/extract-text", response_model=SingleOCRResponse)
async def extract_text(image: UploadFile = File(...)):
    try:
        return await process_single_image(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-extract", response_model=BatchOCRResponse)
async def batch_extract(images: List[UploadFile] = File(...)):
    try:
        return await process_batch_images(images)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
