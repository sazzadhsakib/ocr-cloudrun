import pytest
import io
import time
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

# Test images: small examples in tests/images/
TEST_IMAGES = {
    "jpeg": "tests/images/book page.jpg",
    "png": "tests/images/doc_with_formula.png",
    "gif": "tests/images/company-invoice.gif",  # static GIF
    "animated_gif": "tests/images/animated-test-gif.gif",  # expected to fail
    "fail_image": "tests/images/blank.jpg",  # expected to fail
}


@pytest.mark.parametrize("fmt,path", TEST_IMAGES.items())
def test_extract_text_single(fmt, path):
    """Test single image extraction for multiple formats including GIFs and failures."""
    with open(path, "rb") as f:
        files = {"image": (f.name, f, f"image/{fmt}")}
        start = time.time()
        response = client.post("/v1/extract-text", files=files)
        duration = time.time() - start

    # If image is invalid/unsupported, HTTPException is raised with 'detail'
    if fmt in ["animated_gif", "fail_image"]:
        assert response.status_code in [415, 413, 500]
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str) and len(data["detail"]) > 0
        print(f"{fmt.upper()} correctly failed: {data['detail']}")
        return

    data = response.json()
    assert response.status_code == 200
    assert data["success"] is True
    assert "text" in data and len(data["text"]) > 0
    assert 0.0 <= data["confidence"] <= 1.0
    assert "metadata" in data
    assert data["metadata"]["width"] > 0
    assert data["metadata"]["height"] > 0
    assert data["metadata"]["format"].lower() in ["jpeg", "png", "gif"]

    print(f"{fmt.upper()} processed in {duration:.3f}s, confidence: {data['confidence']}")


def test_caching_same_image():
    """Upload the same image twice and ensure second request uses cache."""
    path = TEST_IMAGES["jpeg"]
    with open(path, "rb") as f:
        files = {"image": (f.name, f, "image/jpeg")}
        resp1 = client.post("/v1/extract-text", files=files)

    with open(path, "rb") as f:
        files = {"image": (f.name, f, "image/jpeg")}
        resp2 = client.post("/v1/extract-text", files=files)

    data1 = resp1.json()
    data2 = resp2.json()
    assert data1 == data2
    assert resp2.headers.get("X-Cache-Status") == "cached"


def test_batch_processing():
    """Test batch endpoint with multiple images, including expected failures."""
    files = []
    for fmt, path in TEST_IMAGES.items():
        with open(path, "rb") as f:
            files.append(("images", (f.name, f.read(), f"image/{fmt}")))

    response = client.post("/v1/batch-extract", files=files)
    data = response.json()

    # Should return 207 if any failures
    assert response.status_code in [200, 207]
    assert "results" in data
    assert len(data["results"]) == len(TEST_IMAGES)

    for res in data["results"]:
        assert "filename" in res
        assert "success" in res
        assert "text" in res
        assert "confidence" in res
        assert "metadata" in res
        assert "error" in res  # all images must have error field

        if res["success"]:
            assert 0.0 <= res["confidence"] <= 1.0
            assert res["text"] != ""
        else:
            assert res["error"] is not None
