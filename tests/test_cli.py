"""Unit tests for the CLI interface."""

from pathlib import Path
import pytest

from logo2svg.cli import build_parser, find_image_files, main


def test_build_parser() -> None:
    """Test CLI argument parser configurations."""
    parser = build_parser()
    args = parser.parse_args(["image.png", "--preset", "sharp", "--bw", "--colors", "4", "--scale", "2.0"])
    assert args.input == "image.png"
    assert args.preset == "sharp"
    assert args.bw is True
    assert args.colors == 4
    assert args.scale == 2.0


def test_find_image_files_single(sample_rgb_logo: Path) -> None:
    """Test finding a single image file."""
    files = find_image_files(sample_rgb_logo)
    assert len(files) == 1
    assert files[0] == sample_rgb_logo


def test_find_image_files_dir(temp_dir: Path, sample_rgb_logo: Path, sample_rgba_logo: Path) -> None:
    """Test discovering all images in a directory."""
    files = find_image_files(temp_dir)
    assert len(files) >= 2


def test_cli_convert_single_file(sample_rgba_logo: Path, temp_dir: Path) -> None:
    """Test CLI execution on a single file."""
    out_svg = temp_dir / "cli_test.svg"
    exit_code = main([str(sample_rgba_logo), "-o", str(out_svg), "--preset", "sharp"])
    assert exit_code == 0
    assert out_svg.is_file()
    assert "<path" in out_svg.read_text(encoding="utf-8")


def test_cli_convert_batch_dir(temp_dir: Path, sample_rgb_logo: Path, sample_rgba_logo: Path) -> None:
    """Test CLI execution on an entire folder."""
    out_batch = temp_dir / "batch_out"
    exit_code = main([str(temp_dir), "-o", str(out_batch), "--preset", "logo"])
    assert exit_code == 0
    assert out_batch.is_dir()
    svg_files = list(out_batch.glob("*.svg"))
    assert len(svg_files) >= 2


def test_cli_nonexistent_input(temp_dir: Path) -> None:
    """Test CLI returns error code on nonexistent input."""
    exit_code = main([str(temp_dir / "missing.png")])
    assert exit_code == 1
