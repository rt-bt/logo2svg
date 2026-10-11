"""Benchmark all examples and generate summary metrics table."""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from logo2svg.converter import ConversionOptions, convert_image

examples_dir = Path(__file__).resolve().parent.parent / "examples"

logos = [
    ("geometric_logo.png", "sharp", False, False, None),
    ("smooth_badge.png", "smooth", False, False, None),
    ("tech_shield.png", "logo", False, False, None),
    ("retro_crest.jpg", "logo", False, True, None),
    ("transparent_icon.png", "logo", True, False, None),
]

print(f"{'Input File':<22} | {'Preset':<7} | {'Original':<10} | {'SVG Size':<10} | {'SSIM':<7} | {'Visual Match':<12} | {'PSNR (dB)':<9}")
print("-" * 90)

for filename, preset, keep_alpha, denoise, colors in logos:
    in_path = examples_dir / filename
    out_svg = examples_dir / f"{in_path.stem}.svg"

    opts = ConversionOptions(
        preset=preset,
        keep_alpha=keep_alpha,
        denoise=denoise,
        colors=colors,
        optimize=True,
        check_quality=True,
    )

    res = convert_image(in_path, out_svg, options=opts)
    orig_kb = f"{res.original_size_bytes / 1024:.1f} KB"
    svg_kb = f"{res.svg_size_bytes / 1024:.1f} KB"
    ssim_val = f"{res.comparison.ssim:.4f}"
    pct_val = f"{res.comparison.similarity_percentage:.2f}%"
    psnr_val = f"{res.comparison.psnr:.1f}"

    print(f"{filename:<22} | {preset:<7} | {orig_kb:<10} | {svg_kb:<10} | {ssim_val:<7} | {pct_val:<12} | {psnr_val:<9}")
