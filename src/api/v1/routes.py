from fastapi import APIRouter, UploadFile, File, HTTPException
from src.services.ocr_service import process_single_image, process_batch_images

router = APIRouter()

@router.post("/extract-text")
async def extract_text(image: UploadFile = File(...)):
    try:
        return await process_single_image(image)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-extract")
async def batch_extract(images: list[UploadFile] = File(...)):
    try:
        return await process_batch_images(images)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
