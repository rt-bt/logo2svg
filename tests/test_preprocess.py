"""Unit tests for the image preprocessing pipeline."""

from pathlib import Path
import pytest
from PIL import Image

from logo2svg.preprocess import (
    CorruptedImageError,
    PreprocessResult,
    UnsupportedFormatError,
    auto_upscale,
    binarize_image,
    denoise_image,
    flatten_transparency,
    preprocess_image,
    quantize_colors,
    validate_image_path,
)


def test_validate_image_path_success(sample_rgba_logo: Path) -> None:
    """Test path validation on supported existing file."""
    validated = validate_image_path(sample_rgba_logo)
    assert validated.is_file()


def test_validate_image_path_not_found(temp_dir: Path) -> None:
    """Test FileNotFoundError on nonexistent image path."""
    with pytest.raises(FileNotFoundError):
        validate_image_path(temp_dir / "nonexistent.png")


def test_validate_image_path_unsupported_format(temp_dir: Path) -> None:
    """Test UnsupportedFormatError on invalid extension."""
    txt_file = temp_dir / "notes.txt"
    txt_file.write_text("hello")
    with pytest.raises(UnsupportedFormatError):
        validate_image_path(txt_file)


def test_corrupted_image_handling(corrupted_image_file: Path) -> None:
    """Test CorruptedImageError when loading unreadable file."""
    with pytest.raises(CorruptedImageError):
        preprocess_image(corrupted_image_file)


def test_flatten_transparency(sample_rgba_logo: Path) -> None:
    """Test flattening alpha onto a solid white background."""
    img = Image.open(sample_rgba_logo)
    assert img.mode == "RGBA"

    flattened = flatten_transparency(img)
    assert flattened.mode == "RGB"
    # Corner pixel that was transparent should now be solid white
    corner_pixel = flattened.getpixel((0, 0))
    assert corner_pixel == (255, 255, 255)


def test_auto_upscale() -> None:
    """Test auto-upscaling images smaller than 1000px."""
    small = Image.new("RGB", (200, 300), "white")
    upscaled, factor = auto_upscale(small, target_min_dim=1000, default_multiplier=2.0)
    assert factor == 2.0
    assert upscaled.size == (400, 600)

    # Large image should not auto-upscale
    large = Image.new("RGB", (1200, 1500), "white")
    same, factor2 = auto_upscale(large, target_min_dim=1000)
    assert factor2 == 1.0
    assert same.size == (1200, 1500)


def test_custom_user_scale() -> None:
    """Test explicit user scale multiplier."""
    img = Image.new("RGB", (100, 100), "blue")
    upscaled, factor = auto_upscale(img, user_scale=3.5)
    assert factor == 3.5
    assert upscaled.size == (350, 350)


def test_denoise_image() -> None:
    """Test median filter denoising filter."""
    img = Image.new("RGB", (50, 50), "red")
    denoised = denoise_image(img, filter_size=3)
    assert denoised.size == (50, 50)


def test_quantize_colors() -> None:
    """Test color reduction to specified palette size."""
    img = Image.new("RGB", (80, 80), "blue")
    quantized = quantize_colors(img, num_colors=4)
    assert quantized.size == (80, 80)
    # Check palette has at most 4 colors
    unique_colors = len(quantized.getcolors(maxcolors=256) or [])
    assert unique_colors <= 4


def test_binarize_image() -> None:
    """Test Otsu binarization to pure black and white."""
    img = Image.new("L", (100, 100), color=50)
    # Add a bright region
    for x in range(30, 70):
        for y in range(30, 70):
            img.putpixel((x, y), 220)

    bw = binarize_image(img)
    assert bw.mode == "L"
    colors = set(img_val for count, img_val in bw.getcolors())
    assert colors.issubset({0, 255})


def test_preprocess_pipeline_keep_alpha(sample_rgba_logo: Path) -> None:
    """Test full pipeline with keep_alpha=True."""
    res = preprocess_image(sample_rgba_logo, keep_alpha=True)
    assert isinstance(res, PreprocessResult)
    assert res.has_alpha is True
    assert res.image.mode == "RGBA"
    assert res.scale_factor == 2.0
    assert res.final_size == (240, 240)


def test_preprocess_pipeline_flatten_default(sample_rgba_logo: Path) -> None:
    """Test full pipeline with default flattening."""
    res = preprocess_image(sample_rgba_logo, keep_alpha=False)
    assert isinstance(res, PreprocessResult)
    assert res.has_alpha is False
    assert res.image.mode == "RGB"
    assert res.final_size == (240, 240)
