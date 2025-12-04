# 📄 OCR Cloud Run Service

A **FastAPI-based OCR service** leveraging the **Google Vision API**. It supports single and batch image processing, includes robust validation, intelligent caching, and rate limiting. It's specifically designed for deployment on **Google Cloud Run** but is fully functional for local development.

-----

## ✨ **Features**

  * **Single Image OCR**: Extract text, confidence, metadata, and processing time from a single image (`JPEG`, `PNG`, `GIF`).
  * **Batch Image OCR**: Process multiple images in one request, supporting **partial failures** with a `207 Multi-Status` response.
  * **Image Validation**: Enforces limits on file size (**Max 10 MB**), GIF size (**Max 10 MB**), and GIF frames (**Max 50**), files count(**Max 10**) for batch processing
  * **Preprocessing**: Includes **contrast enhancement** and ensures consistency by converting images to JPEG before OCR.
  * **Caching**: Utilizes an **in-memory cache** with a TTL (`CACHE_TTL=7200s`) to reuse results and improve performance.
  * **Rate Limiting**:
      * Single image: 60 requests/min per IP.
      * Batch image: 30 requests/min per IP.
      * Global: 100 requests/min per IP.
      * Health check is exempt.
  * **Logging**: Structured **JSON logs** are written to `logs/ocr_service.log`.
  * **Health Check**: Dedicated `/v1/health` endpoint.

-----

## 🧱 Project Structure and Standards

This project adheres to **Clean Architecture** principles and implements **SOLID** design patterns to ensure maintainability, scalability, and testability.

* **Separation of Concerns**: Core business logic is isolated in the `src/services` layer, separate from the API definitions in `src/api`.
* **Layered Design**:
    * `src/api`: Handles HTTP request routing and validation.
    * `src/services`: Contains core use cases and business logic (e.g., `ocr_service.py`).
    * `src/models`: Defines data structures for consistent input/output.
    * `src/middleware`: Manages cross-cutting concerns like rate limiting.
* **Testing**: Includes a dedicated test suite (`test_ocr_service.py`) and test assets for robust validation.

-----

## 🚀 **API Endpoints**

### 1\. Single Image OCR

`POST /v1/extract-text`

Test Single Image OCR

```bash
# Replace the path with a valid image path on your local machine
curl --location 'https://ocr-service-240440546630.us-central1.run.app/v1/extract-text' \
--form 'image=@"/C:/Users/sazzad/Downloads/invoice2x.jpg"'
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| **image** | file | Yes | The image file for OCR (JPEG, PNG, GIF). |

**Response**: `200 OK` (SingleOCRResponse)

```json
{
  "success": true,
  "text": "Detected text",
  "confidence": 0.98,
  "metadata": {
    "width": 1200,
    "height": 800,
    "format": "JPEG",
    "mimetype": "image/jpeg"
  },
  "processing_time_ms": 150
}
```

### 2\. Batch Image OCR

`POST /v1/batch-extract`

```bash
# Replace the path with a valid image path on your local machine
curl --location 'https://ocr-service-240440546630.us-central1.run.app/v1/batch-extract' \
--header 'accept: application/json' \
--form 'images=@"/C:/Users/sazzad/Downloads/book page.jpg"' \
--form 'images=@"/C:/Users/sazzad/Downloads/inguodo-inc.jpg"' \
--form 'images=@"/C:/Users/sazzad/Downloads/book.jpg"'

````


| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| **images** | file\[] | Yes | An array of image files (max 10) for batch processing. |

**Response**: `200 OK` (BatchOCRResponse) or **`207 Multi-Status`** on partial failure.

```json
{
  "success": false,
  "total_images": 3,
  "total_processing_time_ms": 450,
  "results": [
    {
      "filename": "doc1.jpg",
      "success": true,
      "text": "Hello World",
      "confidence": 0.95,
      "error": null
    },
    {
      "filename": "doc2.gif",
      "success": false,
      "text": "",
      "error": "No text detected in image."
    }
  ]
}
```

### 3\. Health Check

`GET /v1/health`

**Response**:

```json
{
  "status": "healthy",
  "service": "ocr-api"
}
```

-----

## 💻 **Running Locally (Python)**

1.  **Create and activate virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    # .\venv\Scripts\activate  # Windows
    ```

2.  **Install dependencies:**

    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

3.  **Set Google credentials:**

    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="path/to/google-service-account.json"
    ```

4.  **Run FastAPI:**

    ```bash
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload
    ```

## 🐳 **Running Locally (Docker)**

1.  **Build Docker image:**

    ```bash
    docker build -t ocr-service:latest .
    ```

2.  **Run container (Remember to mount your credentials):**

    ```bash
    docker run -it --rm \
      -p 8000:8000 \
      -e GOOGLE_APPLICATION_CREDENTIALS="/app/path/to/google-service-account.json" \
      -v /local/path/to/google-service-account.json:/app/path/to/google-service-account.json \
      ocr-service:latest
    ```

-----

## ☁️ **Deploy to GCP Cloud Run**

### 1\. Build and push image

Replace `ocr-cloud-engine/ocr-repo` with your GCP project and Artifact Registry repo path.

```bash
docker build -t us-central1-docker.pkg.dev/ocr-cloud-engine/ocr-repo/ocr-service:latest .
docker push us-central1-docker.pkg.dev/ocr-cloud-engine/ocr-repo/ocr-service:latest
```

### 2\. Deploy service

This configuration is optimized for testing and cost control.

| Setting | Value | Note |
| :--- | :--- | :--- |
| **Public access** | `--allow-unauthenticated` | Fully public for testing purposes. |
| **Concurrency** | `--concurrency 3` | Limited to 3 requests per container. |
| **Scaling** | `--max-instances 1` | Only 1 container deployed to control costs. |
| **Resources** | `--memory 1Gi`, `--cpu 2` | Generous resources for fast OCR. |
| **Service Account** | `--service-account ocr-service-account@...` | Must have **Cloud Vision API User** role. |

```bash
gcloud run deploy ocr-service \
  --image us-central1-docker.pkg.dev/ocr-cloud-engine/ocr-repo/ocr-service:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account ocr-service-account@ocr-cloud-engine.iam.gserviceaccount.com \
  --memory 1Gi \
  --cpu 2 \
  --concurrency 3 \
  --max-instances 1 \
  --timeout 120
```

-----

## 🧪 **Testing**

The service includes a comprehensive test suite to ensure functionality.

```bash
pytest test_ocr_service.py
```

Tests validate:

  * Single image OCR and batch processing.
  * Caching mechanism (cache hits/misses).
  * Correct error handling (e.g., file size limits, unsupported formats).
  * Support for JPEG, PNG, and static GIFs.


## 📜 **Logging**

Logs are stored in structured **JSON** format at `logs/ocr_service.log`. This log file captures:

  * Cache hit/miss events.
  * Image preprocessing details.
  * Request processing times.
  * Rate limit violations.


