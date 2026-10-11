"""Unit tests for the vector tracing module."""

from pathlib import Path
import re
import pytest
from PIL import Image

from logo2svg.trace import TraceConfig, TraceError, TracePreset, trace_image


def test_trace_preset_enum() -> None:
    """Test valid preset values and string conversion."""
    assert TracePreset.LOGO == "logo"
    assert TracePreset.SHARP == "sharp"
    assert TracePreset.SMOOTH == "smooth"


def test_trace_config_presets() -> None:
    """Test config parameters generated from different presets."""
    cfg_logo = TraceConfig.from_preset(TracePreset.LOGO)
    assert cfg_logo.mode == "spline"
    assert cfg_logo.colormode == "color"

    cfg_sharp = TraceConfig.from_preset(TracePreset.SHARP)
    assert cfg_sharp.mode == "polygon"

    cfg_smooth = TraceConfig.from_preset(TracePreset.SMOOTH)
    assert cfg_smooth.mode == "spline"
    assert cfg_smooth.corner_threshold == 90

    cfg_bw = TraceConfig.from_preset(TracePreset.LOGO, bw=True)
    assert cfg_bw.colormode == "binary"

    cfg_colors = TraceConfig.from_preset(TracePreset.LOGO, colors=4)
    assert cfg_colors.color_precision == 4


def test_trace_image_basic(sample_rgb_logo: Path) -> None:
    """Test tracing an image to SVG string."""
    svg = trace_image(sample_rgb_logo, preset=TracePreset.LOGO)
    assert isinstance(svg, str)
    assert svg.strip().startswith("<?xml") or "<svg" in svg
    assert "<path" in svg
    assert "<image" not in svg  # Ensure no raster images


def test_trace_image_to_file(sample_rgb_logo: Path, temp_dir: Path) -> None:
    """Test tracing an image and saving to output path."""
    out_svg = temp_dir / "traced_output.svg"
    svg = trace_image(sample_rgb_logo, output_path=out_svg, preset=TracePreset.SHARP)
    assert out_svg.is_file()
    assert out_svg.stat().st_size > 0
    assert svg == out_svg.read_text(encoding="utf-8")


def test_trace_image_bw_mode(sample_rgb_logo: Path) -> None:
    """Test binary tracing mode."""
    svg = trace_image(sample_rgb_logo, bw=True)
    assert "<path" in svg
    assert "<image" not in svg


def test_trace_image_from_pil_image() -> None:
    """Test tracing directly from a PIL Image in memory."""
    img = Image.new("RGB", (60, 60), "red")
    svg = trace_image(img, preset=TracePreset.LOGO)
    assert "<path" in svg


def test_trace_nonexistent_file(temp_dir: Path) -> None:
    """Test FileNotFoundError when passing missing image path."""
    with pytest.raises(FileNotFoundError):
        trace_image(temp_dir / "does_not_exist.png")
