"""Unit tests for the SVG quality rendering and SSIM comparison module."""

from pathlib import Path
import numpy as np
import pytest
from PIL import Image

from logo2svg.compare import (
    ComparisonResult,
    calculate_psnr,
    compare_svg_to_image,
    render_svg_to_image,
)


def test_calculate_psnr_identical() -> None:
    """Test PSNR of identical images is infinity."""
    arr = np.zeros((50, 50), dtype=np.uint8)
    psnr = calculate_psnr(arr, arr)
    assert psnr == float("inf")


def test_calculate_psnr_different() -> None:
    """Test PSNR of distinct images."""
    arr1 = np.zeros((50, 50), dtype=np.uint8)
    arr2 = np.ones((50, 50), dtype=np.uint8) * 10
    psnr = calculate_psnr(arr1, arr2)
    assert 20.0 < psnr < 40.0


def test_render_svg_to_image() -> None:
    """Test rasterizing an SVG string back to a PIL image."""
    svg = '<svg viewBox="0 0 100 100" width="100" height="100"><rect width="100" height="100" fill="red"/></svg>'
    img, renderer = render_svg_to_image(svg, target_width=100, target_height=100)
    assert isinstance(img, Image.Image)
    assert img.size == (100, 100)
    assert renderer in ("cairosvg", "resvg")


def test_compare_svg_to_image(sample_rgba_logo: Path) -> None:
    """Test SSIM comparison against a reference image."""
    # Create an SVG that represents the image
    svg = '<svg viewBox="0 0 120 120" width="120" height="120"><rect width="120" height="120" fill="white"/></svg>'
    result = compare_svg_to_image(svg, sample_rgba_logo)
    assert isinstance(result, ComparisonResult)
    assert 0.0 <= result.ssim <= 1.0
    assert 0.0 <= result.similarity_percentage <= 100.0
    assert result.psnr > 0.0
    assert isinstance(result.rendered_image, Image.Image)
    assert str(result).startswith("Quality Score:")
