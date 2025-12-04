# app/main.py
import time
from fastapi import FastAPI, File, UploadFile, HTTPException
from google.cloud import vision
from PIL import Image
import io

app = FastAPI(title="OCR Cloud Run Challenge - Local")

# create client (uses GOOGLE_APPLICATION_CREDENTIALS)
client = vision.ImageAnnotatorClient()

@app.post("/extract-text")
async def extract_text(image: UploadFile = File(...)):
    # basic validation
    if image.content_type not in ("image/jpeg", "image/jpg", "image/png", "image/gif"):
        raise HTTPException(status_code=415, detail="Unsupported file type.")
    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large.")

    start = time.time()
    # prepare image for Vision API
    vision_image = vision.Image(content=contents)

    response = client.text_detection(image=vision_image)
    annotations = response.text_annotations

    if response.error.message:
        raise HTTPException(status_code=500, detail=response.error.message)

    extracted_text = annotations[0].description if annotations else ""
    # confidence is not directly in text_annotations top-level; you can aggregate from pages/blocks if desired
    processing_time_ms = int((time.time() - start) * 1000)

    return {
        "success": bool(extracted_text),
        "text": extracted_text,
        "confidence": None,   # we'll compute a confidence later
        "processing_time_ms": processing_time_ms
    }
