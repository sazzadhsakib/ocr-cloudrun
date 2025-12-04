from PIL import Image
import io

def extract_metadata(raw_bytes: bytes, original_format: str, mimetype: str):
    """
    Extract image metadata for OCR.
    raw_bytes: preprocessed bytes (JPEG for Vision)
    original_format: original uploaded format (PNG, GIF, etc.)
    mimetype: original uploaded mimetype (image/png etc.)
    """
    img = Image.open(io.BytesIO(raw_bytes))
    return {"width": img.width, "height": img.height, "format": original_format, "mimetype": mimetype}
