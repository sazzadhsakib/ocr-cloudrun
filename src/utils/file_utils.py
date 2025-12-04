from fastapi import UploadFile, HTTPException
from PIL import Image, UnidentifiedImageError
import io
from src.config import settings

ALLOWED_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/gif"]

async def validate_file(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type.")
    contents = await file.read()
    _validate_image_bytes(contents, file.content_type)
    return contents

def _validate_image_bytes(contents: bytes, content_type: str):
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type.")

    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large.")

    if content_type == "image/gif" and len(contents) > settings.MAX_GIF_SIZE:
        raise HTTPException(status_code=413, detail="GIF too large.")

    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()
        img = Image.open(io.BytesIO(contents))
        n_frames = getattr(img, "n_frames", 1)
        if content_type == "image/gif" and n_frames > settings.MAX_GIF_FRAMES:
            raise HTTPException(status_code=415, detail="Animated GIFs are not supported. Upload a static image.")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file appears to be corrupted or unreadable.")
