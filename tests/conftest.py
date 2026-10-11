"""Pytest fixtures for logo2svg tests."""

import sys
import tempfile
from pathlib import Path
from typing import Generator

# Ensure src/ is first in sys.path so the logo2svg package takes precedence
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path in sys.path:
    sys.path.remove(src_path)
sys.path.insert(0, src_path)

import pytest
from PIL import Image, ImageDraw


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def sample_rgba_logo(temp_dir: Path) -> Path:
    """Create a sample RGBA PNG logo with transparency."""
    img = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Red circle
    d.ellipse([20, 20, 100, 100], fill=(239, 68, 68, 255))
    # Blue square inside
    d.rectangle([40, 40, 80, 80], fill=(59, 130, 246, 255))
    path = temp_dir / "sample_rgba.png"
    img.save(path, format="PNG")
    return path


@pytest.fixture
def sample_rgb_logo(temp_dir: Path) -> Path:
    """Create a sample solid RGB JPEG logo."""
    img = Image.new("RGB", (150, 150), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.polygon([(75, 20), (130, 130), (20, 130)], fill=(16, 185, 129))
    path = temp_dir / "sample_rgb.jpg"
    img.save(path, format="JPEG", quality=80)
    return path


@pytest.fixture
def corrupted_image_file(temp_dir: Path) -> Path:
    """Create a corrupted/unreadable image file."""
    path = temp_dir / "corrupted.png"
    with open(path, "wb") as f:
        f.write(b"NOT_A_REAL_PNG_HEADER_DATA_1234567890")
    return path
