from PIL import Image, ImageEnhance, UnidentifiedImageError
import io
from src.config import settings

def preprocess_image(raw_bytes: bytes):
    try:
        image = Image.open(io.BytesIO(raw_bytes))
    except UnidentifiedImageError:
        raise ValueError("Invalid or corrupted image file.")

    original_format = image.format

    if image.format == "GIF":
        try:
            image.seek(0)
            if getattr(image, "n_frames", 1) > settings.MAX_GIF_FRAMES:
                raise ValueError("GIF has too many frames.")
            image = image.convert("RGB")
        except Exception as e:
            raise ValueError(f"GIF processing failed: {str(e)}")

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(settings.CONTRAST_ENHANCE_FACTOR)

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=settings.JPEG_QUALITY)
    return output.getvalue(), original_format
