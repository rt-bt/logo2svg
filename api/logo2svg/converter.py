"""High-level conversion coordinator for logo2svg.

Combines preprocessing, vector tracing, post-processing optimization,
and quality verification into a seamless pipeline.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from PIL import Image

from .compare import ComparisonResult, compare_svg_to_image
from .optimize import optimize_svg
from .preprocess import PreprocessResult, preprocess_image
from .trace import TraceConfig, TracePreset, trace_image


@dataclass
class ConversionOptions:
    """Options controlling the logo conversion pipeline."""

    preset: Union[str, TracePreset] = TracePreset.LOGO
    bw: bool = False
    colors: Optional[int] = None
    scale: Optional[float] = None
    keep_alpha: bool = False
    denoise: bool = False
    precision: int = 2
    minify: bool = False
    optimize: bool = True
    check_quality: bool = True


@dataclass
class ConversionResult:
    """Result and metrics of a logo conversion operation."""

    svg_content: str
    output_path: Optional[Path]
    preprocess: PreprocessResult
    comparison: Optional[ComparisonResult]
    original_size_bytes: int
    svg_size_bytes: int

    @property
    def ssim(self) -> Optional[float]:
        """Convenience property for SSIM score."""
        return self.comparison.ssim if self.comparison else None

    @property
    def similarity_percentage(self) -> Optional[float]:
        """Convenience property for similarity percentage."""
        return self.comparison.similarity_percentage if self.comparison else None


def convert_image(
    input_path: Union[str, Path, Image.Image],
    output_path: Optional[Union[str, Path]] = None,
    options: Optional[ConversionOptions] = None,
) -> ConversionResult:
    """Convert a raster logo to an optimized SVG vector file.

    Args:
        input_path: File path to raster image or PIL Image object.
        output_path: Optional file path where the generated SVG should be saved.
        options: ConversionOptions configuring the pipeline.

    Returns:
        ConversionResult containing SVG content and quality metrics.
    """
    if options is None:
        options = ConversionOptions()

    # Determine original file size if reading from disk
    orig_file_size = 0
    if isinstance(input_path, (str, Path)):
        p = Path(input_path)
        if p.is_file():
            orig_file_size = p.stat().st_size

    # Step 1: Preprocessing pipeline
    pre = preprocess_image(
        image_input=input_path,
        keep_alpha=options.keep_alpha,
        scale=options.scale,
        denoise=options.denoise,
        colors=options.colors,
        bw=options.bw,
    )

    # Step 2: Vector tracing
    raw_svg = trace_image(
        image_input=pre.image,
        output_path=None,  # We optimize before writing to final destination
        preset=options.preset,
        bw=options.bw,
        colors=options.colors,
    )

    # Step 3: SVG post-processing & optimization
    if options.optimize:
        final_svg = optimize_svg(
            raw_svg,
            precision=options.precision,
            minify=options.minify,
            coord_width=float(pre.final_size[0]),
            coord_height=float(pre.final_size[1]),
            display_width=float(pre.original_size[0]),
            display_height=float(pre.original_size[1]),
        )
    else:
        final_svg = raw_svg

    # Step 4: Write to output file if requested
    target_out_path = None
    if output_path is not None:
        target_out_path = Path(output_path).resolve()
        target_out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_out_path, "w", encoding="utf-8") as f:
            f.write(final_svg)

    # Step 5: Quality check with SSIM
    comparison = None
    if options.check_quality:
        comparison = compare_svg_to_image(
            svg_input=final_svg,
            reference_image=input_path,
        )

    svg_bytes_count = len(final_svg.encode("utf-8"))

    return ConversionResult(
        svg_content=final_svg,
        output_path=target_out_path,
        preprocess=pre,
        comparison=comparison,
        original_size_bytes=orig_file_size,
        svg_size_bytes=svg_bytes_count,
    )
