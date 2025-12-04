from fastapi import UploadFile, HTTPException

ALLOWED_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/gif"]

async def validate_file(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type.")
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large.")
    return contents

