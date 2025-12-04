import pytest
import io
import time
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

# Test images: provide small example images in your tests/images/ folder
TEST_IMAGES = {
    "jpeg": "tests/images/book page.jpg",
    "png": "tests/images/doc_with_formula.png",
    "gif": "tests/images/company-invoice.gif",
}


@pytest.mark.parametrize("fmt,path", TEST_IMAGES.items())
def test_extract_text_single(fmt, path):
    """
    Test single image extraction for multiple formats.
    Checks success, confidence, and metadata.
    """
    with open(path, "rb") as f:
        files = {"image": (f.name, f, f"image/{fmt}")}
        start = time.time()
        response = client.post("/v1/extract-text", files=files)
        duration = time.time() - start

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "text" in data and len(data["text"]) > 0
    assert "confidence" in data
    # Confidence should be a float between 0 and 1
    assert isinstance(data["confidence"], float)
    assert 0.0 < data["confidence"] <= 1.0
    assert "metadata" in data
    assert data["metadata"]["width"] > 0
    assert data["metadata"]["height"] > 0
    assert data["metadata"]["format"].lower() in ["jpeg", "png"]

    print(f"Processing time: {duration:.3f}s, confidence: {data['confidence']}")


def test_caching_same_image():
    """
    Upload the same image twice and check that the second request is faster.
    """
    path = TEST_IMAGES["jpeg"]
    with open(path, "rb") as f:
        files = {"image": (f.name, f, "image/jpeg")}
        start1 = time.time()
        resp1 = client.post("/v1/extract-text", files=files)
        duration1 = time.time() - start1

    # Rewind file and send again
    with open(path, "rb") as f:
        files = {"image": (f.name, f, "image/jpeg")}
        start2 = time.time()
        resp2 = client.post("/v1/extract-text", files=files)
        duration2 = time.time() - start2

    data1 = resp1.json()
    data2 = resp2.json()
    assert data1 == data2, "Cached result should match original result"
    assert duration2 <= duration1, "Second request should be faster due to cache"


def test_batch_processing():
    """
    Test batch endpoint with multiple images
    """
    files = []
    for fmt, path in TEST_IMAGES.items():
        with open(path, "rb") as f:
            files.append(("images", (f.name, f.read(), f"image/{fmt}")))

    response = client.post("/v1/batch-extract", files=files)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(TEST_IMAGES)

    for result in data:
        assert result["success"] is True
        assert "text" in result and len(result["text"]) > 0
        assert 0.0 < result["confidence"] <= 1.0
        assert "metadata" in result
