from PIL import Image, ImageEnhance
import io


def preprocess_image(raw_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(raw_bytes))
    original_format = image.format  # PNG, GIF, etc.

    # Convert GIF to RGB
    if image.format == "GIF":
        image = image.convert("RGB")

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)

    # Convert to bytes for Vision API
    output = io.BytesIO()
    image.save(output, format="JPEG")
    processed_bytes = output.getvalue()

    return processed_bytes, original_format
