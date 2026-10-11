"""Unit tests for the SVG post-processing and optimization module."""

from pathlib import Path
import pytest

from logo2svg.optimize import (
    SvgOptimizationError,
    ensure_viewbox,
    extract_dimensions_from_svg,
    optimize_svg,
    optimize_svg_file,
    round_path_data,
    verify_pure_vector,
)


def test_round_path_data() -> None:
    """Test rounding coordinates in path data strings."""
    raw_d = "M 10.12345 20.6789 C 30.55555 40.44444 50.00000 60.11111"
    rounded = round_path_data(raw_d, precision=2)
    assert rounded == "M 10.12 20.68 C 30.56 40.44 50 60.11"


def test_extract_dimensions_from_svg() -> None:
    """Test extracting width and height from SVG tag."""
    svg = '<svg version="1.1" width="500" height="400"><path d="M0 0"/></svg>'
    w, h = extract_dimensions_from_svg(svg)
    assert w == 500.0
    assert h == 400.0


def test_ensure_viewbox_insertion() -> None:
    """Test viewBox attribute is added if missing."""
    svg = '<svg version="1.1" width="300" height="200"><path d="M0 0"/></svg>'
    with_vb = ensure_viewbox(svg)
    assert 'viewBox="0 0 300 200"' in with_vb


def test_ensure_viewbox_preserved() -> None:
    """Test existing viewBox attribute is not overwritten."""
    svg = '<svg viewBox="0 0 100 100" width="300" height="200"><path d="M0 0"/></svg>'
    with_vb = ensure_viewbox(svg)
    assert 'viewBox="0 0 100 100"' in with_vb


def test_ensure_viewbox_with_display_dimensions() -> None:
    """Test updating width/height while preserving coordinate viewBox."""
    svg = '<svg width="800" height="800"><path d="M0 0"/></svg>'
    result = ensure_viewbox(
        svg,
        coord_width=800,
        coord_height=800,
        display_width=400,
        display_height=400,
    )
    assert 'viewBox="0 0 800 800"' in result
    assert 'width="400"' in result
    assert 'height="400"' in result


def test_verify_pure_vector_valid() -> None:
    """Test valid SVG with path passes verification."""
    svg = '<svg viewBox="0 0 100 100"><path d="M0 0 L10 10 Z"/></svg>'
    verify_pure_vector(svg)  # Should not raise


def test_verify_pure_vector_rejects_embedded_image() -> None:
    """Test rejection of SVGs containing <image> tags."""
    svg = '<svg><image href="data:image/png;base64,123"/></svg>'
    with pytest.raises(SvgOptimizationError):
        verify_pure_vector(svg)


def test_verify_pure_vector_rejects_data_uri() -> None:
    """Test rejection of SVGs containing data:image URIs."""
    svg = '<svg><rect fill="data:image/jpeg;base64,123"/></svg>'
    with pytest.raises(SvgOptimizationError):
        verify_pure_vector(svg)


def test_optimize_svg_end_to_end() -> None:
    """Test complete SVG optimization."""
    raw = (
        '<?xml version="1.0"?>\n'
        '<!-- Generator: vtracer -->\n'
        '<svg width="100" height="100">\n'
        '<path d="M 0.1234 0.5678 L 10.9999 10.0001 Z" fill="#ff0000" transform="translate(0,0)"/>\n'
        '</svg>'
    )
    opt = optimize_svg(raw, precision=2)
    assert 'viewBox="0 0 100 100"' in opt
    assert 'transform="translate(0,0)"' not in opt
    assert 'Generator:' not in opt
    assert "0.12" in opt
    assert "0.57" in opt
    assert "<path" in opt


def test_optimize_svg_file(temp_dir: Path) -> None:
    """Test optimizing SVG file from disk."""
    raw = '<svg width="50" height="50"><path d="M 1.2345 2.3456 Z"/></svg>'
    in_file = temp_dir / "in.svg"
    out_file = temp_dir / "out.svg"
    in_file.write_text(raw, encoding="utf-8")

    optimize_svg_file(in_file, out_file, precision=1)
    assert out_file.is_file()
    content = out_file.read_text(encoding="utf-8")
    assert 'viewBox="0 0 50 50"' in content
    assert "1.2" in content
