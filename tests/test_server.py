"""Tests for logo2svg Creative Studio web server API."""

import io
from pathlib import Path
import pytest
from server import app


@pytest.fixture
def client():
    """Create Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_page(client):
    """Test index page returns HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"LOGO2SVG" in response.data or b"Creative Studio" in response.data


def test_get_samples_api(client):
    """Test GET /api/samples returns sample logo list."""
    response = client.get("/api/samples")
    assert response.status_code == 200
    data = response.get_json()
    assert "samples" in data
    assert len(data["samples"]) >= 1
    sample_ids = [s["id"] for s in data["samples"]]
    assert "geometric_logo" in sample_ids


def test_get_sample_file(client):
    """Test GET /api/sample/<filename> serves image."""
    response = client.get("/api/sample/geometric_logo.png")
    assert response.status_code == 200
    assert response.mimetype.startswith("image/")


def test_get_sample_file_not_found(client):
    """Test 404 on missing sample file."""
    response = client.get("/api/sample/non_existent_logo.png")
    assert response.status_code == 404


def test_convert_with_sample(client):
    """Test POST /api/convert with sample logo."""
    response = client.post(
        "/api/convert",
        data={
            "sample": "geometric_logo.png",
            "preset": "logo",
            "bw": "false",
            "minify": "true",
            "precision": "2",
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "<svg" in data["svg_content"]
    assert data["path_count"] > 0
    assert data["ssim_percentage"] > 90.0
    assert "original_data_url" in data


def test_convert_with_file_upload(client):
    """Test POST /api/convert with uploaded file."""
    sample_path = Path("examples/tech_shield.png")
    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/convert",
        data={
            "file": (io.BytesIO(file_bytes), "my_shield.png"),
            "preset": "sharp",
            "bw": "false",
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["filename"] == "my_shield"
    assert data["ssim_percentage"] > 90.0


def test_convert_no_input(client):
    """Test POST /api/convert fails gracefully with 400 when no image is provided."""
    response = client.post("/api/convert", data={})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
