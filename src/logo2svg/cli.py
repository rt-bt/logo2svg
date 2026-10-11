"""Command-line interface (CLI) for logo2svg.

Supports single-file and batch directory conversion with comprehensive
tuning flags (--preset, --bw, --colors, --scale, --keep-alpha, --denoise).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional

from . import __version__
from .converter import ConversionOptions, convert_image
from .preprocess import SUPPORTED_EXTENSIONS, PreprocessError
from .trace import TracePreset


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for logo2svg CLI."""
    parser = argparse.ArgumentParser(
        prog="logo2svg",
        description="Convert raster logos (PNG, JPG, WEBP, BMP) into clean, accurate, scalable SVG vector graphics.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "input",
        type=str,
        help="Input image file path or directory of images for batch conversion.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output SVG file path or directory (default: same as input with .svg extension).",
    )

    parser.add_argument(
        "--preset",
        type=str,
        choices=["logo", "sharp", "smooth"],
        default="logo",
        help="Tracing preset: 'logo' (balanced curves), 'sharp' (polygons/geometric), or 'smooth' (fluid badges).",
    )

    parser.add_argument(
        "--bw",
        action="store_true",
        help="Binary mode: convert logo to clean black-and-white vector paths.",
    )

    parser.add_argument(
        "--colors",
        type=int,
        default=None,
        choices=range(1, 9),
        metavar="1-8",
        help="Quantize to N distinct colors (1-8) before vector tracing to clean noise.",
    )

    parser.add_argument(
        "--scale",
        type=float,
        default=None,
        help="Upscale multiplier (e.g. 2.0). If omitted, small images (<1000px) auto-upscale 2x via LANCZOS.",
    )

    parser.add_argument(
        "--keep-alpha",
        action="store_true",
        help="Preserve transparency instead of flattening onto a solid white background.",
    )

    parser.add_argument(
        "--denoise",
        action="store_true",
        help="Apply median filter denoising to eliminate JPG compression artifacts.",
    )

    parser.add_argument(
        "--precision",
        type=int,
        default=2,
        help="Decimal coordinate precision for path coordinates in SVG.",
    )

    parser.add_argument(
        "--minify",
        action="store_true",
        help="Minify SVG output into compact single-line representation.",
    )

    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Skip SVG post-processing and coordinate optimization.",
    )

    parser.add_argument(
        "--no-check",
        action="store_true",
        help="Skip SSIM quality comparison against original image.",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def format_bytes(num_bytes: int) -> str:
    """Format bytes into human-readable string."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    else:
        return f"{num_bytes / (1024 * 1024):.2f} MB"


def find_image_files(input_path: Path) -> List[Path]:
    """Find all supported image files in input path or directory."""
    if input_path.is_file():
        if input_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            return [input_path]
        return []

    if input_path.is_dir():
        files: List[Path] = []
        for ext in SUPPORTED_EXTENSIONS:
            files.extend(input_path.glob(f"*{ext}"))
            files.extend(input_path.glob(f"*{ext.upper()}"))
        return sorted(set(files))

    return []


def get_status_symbols() -> tuple[str, str]:
    """Return status symbols safe for current terminal encoding."""
    try:
        "\u2713".encode(sys.stdout.encoding or "utf-8")
        return "\u2713", "\u2717"
    except (UnicodeEncodeError, LookupError):
        return "[OK]", "[ERR]"


def process_single_file(
    input_file: Path,
    output_dest: Optional[Path],
    options: ConversionOptions,
    is_batch: bool = False,
) -> bool:
    """Process a single image file to SVG and display summary."""
    sym_ok, sym_err = get_status_symbols()

    # Determine target output file
    if output_dest is None:
        target_svg = input_file.with_suffix(".svg")
    elif output_dest.is_dir() or is_batch:
        output_dest.mkdir(parents=True, exist_ok=True)
        target_svg = output_dest / f"{input_file.stem}.svg"
    else:
        target_svg = output_dest

    start_time = time.time()
    try:
        result = convert_image(
            input_path=input_file,
            output_path=target_svg,
            options=options,
        )
        elapsed = time.time() - start_time

        in_size_str = format_bytes(result.original_size_bytes)
        out_size_str = format_bytes(result.svg_size_bytes)

        print(f"{sym_ok} {input_file.name} -> {target_svg.name}")
        print(f"  Dimensions: {result.preprocess.original_size[0]}x{result.preprocess.original_size[1]}px "
              f"(scale: {result.preprocess.scale_factor:.1f}x) | Size: {in_size_str} -> {out_size_str}")

        if result.comparison:
            ssim_pct = result.comparison.similarity_percentage
            psnr_val = result.comparison.psnr
            print(f"  Accuracy:   {ssim_pct:.2f}% match (SSIM: {result.comparison.ssim:.4f}, PSNR: {psnr_val:.1f} dB)")

        print(f"  Time:       {elapsed:.2f}s")
        return True

    except Exception as e:
        print(f"{sym_err} Error processing {input_file.name}: {e}", file=sys.stderr)
        return False


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1

    output_dest = Path(args.output).resolve() if args.output else None

    # Collect image files
    image_files = find_image_files(input_path)
    if not image_files:
        print(
            f"Error: No supported images found at '{input_path}'. "
            f"Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            file=sys.stderr,
        )
        return 1

    is_batch = len(image_files) > 1 or input_path.is_dir()

    options = ConversionOptions(
        preset=args.preset,
        bw=args.bw,
        colors=args.colors,
        scale=args.scale,
        keep_alpha=args.keep_alpha,
        denoise=args.denoise,
        precision=args.precision,
        minify=args.minify,
        optimize=not args.no_optimize,
        check_quality=not args.no_check,
    )

    print(f"logo2svg v{__version__} | Preset: {args.preset} | Optimizing: {not args.no_optimize}")
    if is_batch:
        print(f"Found {len(image_files)} image(s) to convert in batch...")
    print("-" * 60)

    success_count = 0
    for img_file in image_files:
        if process_single_file(img_file, output_dest, options, is_batch=is_batch):
            success_count += 1
        if is_batch:
            print("-" * 60)

    if is_batch:
        print(f"Completed: {success_count}/{len(image_files)} converted successfully.")

    return 0 if success_count == len(image_files) else 1


if __name__ == "__main__":
    sys.exit(main())
