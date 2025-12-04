from PIL import Image, ImageEnhance, UnidentifiedImageError
import io

MAX_GIF_FRAMES = 50  # safety guard – prevents DoS


def preprocess_image(raw_bytes: bytes):
    try:
        image = Image.open(io.BytesIO(raw_bytes))
    except UnidentifiedImageError:
        raise ValueError("Invalid or corrupted image file.")

    original_format = image.format  # PNG, GIF, JPEG, etc.

    # --- GIF Handling ---
    if image.format == "GIF":
        try:
            # If animated, take only the first frame
            image.seek(0)

            # Safety: reject too many frames
            if getattr(image, "n_frames", 1) > MAX_GIF_FRAMES:
                raise ValueError("GIF has too many frames.")

            # Convert GIF frame to RGB
            image = image.convert("RGB")

        except Exception as e:
            raise ValueError(f"GIF processing failed: {str(e)}")

    # --- Basic Enhancements ---
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)

    # --- Convert final image to JPEG for Vision API ---
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=90)
    processed_bytes = output.getvalue()

    return processed_bytes, original_format
