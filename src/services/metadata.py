from PIL import Image
import io


def extract_metadata(raw_bytes: bytes, original_format: str):
    """
    Extract image metadata for OCR.
    Args:
        raw_bytes: preprocessed image bytes (JPEG for Vision API)
        original_format: format of the original uploaded image (PNG, GIF, JPEG, etc.)
    Returns:
        dict containing width, height, and original format
    """
    img = Image.open(io.BytesIO(raw_bytes))
    return {"width": img.width, "height": img.height, "format": original_format}
