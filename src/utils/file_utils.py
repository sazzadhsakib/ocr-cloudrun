from fastapi import UploadFile, HTTPException
from PIL import Image, UnidentifiedImageError
import io

ALLOWED_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/gif"]

# Max upload size (10MB) kept; GIFs get stricter limit below
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_GIF_SIZE = 3 * 1024 * 1024  # 3 MB for GIFs (configurable)

async def validate_file(file: UploadFile):
    """
    Validate UploadFile (used when we haven't pre-read contents).
    Returns raw bytes on success, raises HTTPException on failure.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type.")
    contents = await file.read()
    _validate_image_bytes(contents, file.content_type)
    return contents

def _validate_image_bytes(contents: bytes, content_type: str):
    """
    Validate raw image bytes. Raises HTTPException if invalid.
    """
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type.")

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large.")

    # Special handling for GIFs (reject large/animated GIFs)
    if content_type == "image/gif":
        if len(contents) > MAX_GIF_SIZE:
            raise HTTPException(status_code=413, detail="GIF too large.")
    try:
        img = Image.open(io.BytesIO(contents))
        # verify may not read the full image, but detects corrupted files
        img.verify()
        # Reopen to access properties (verify puts file object in unusable state)
        img = Image.open(io.BytesIO(contents))
        # If GIF has multiple frames, treat as animated and reject
        n_frames = getattr(img, "n_frames", 1)
        if content_type == "image/gif" and n_frames > 1:
            raise HTTPException(status_code=415, detail="Animated GIFs are not supported. Upload a static image.")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    except HTTPException:
        raise
    except Exception:
        # Generic unreadable/corrupted file
        raise HTTPException(status_code=400, detail="Uploaded file appears to be corrupted or unreadable.")
