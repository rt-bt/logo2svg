"""Vector tracing module using vtracer for logo2svg.

Provides tuned presets ('logo', 'sharp', 'smooth'), black-and-white mode,
and high-fidelity raster-to-vector conversion.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union

import vtracer
from PIL import Image


class TracePreset(str, Enum):
    """Presets optimized for different logo styles."""

    LOGO = "logo"      # Balanced Bézier spline curves for brand logos
    SHARP = "sharp"    # Polygon mode for geometric, angular, tech logos
    SMOOTH = "smooth"  # Gentle spline fitting for badges, organic emblems, and flow


class TraceError(Exception):
    """Raised when an error occurs during vector tracing."""


@dataclass
class TraceConfig:
    """Configuration parameters for vtracer conversion."""

    colormode: str = "color"          # "color" or "binary"
    hierarchical: str = "stacked"     # "stacked" (layered) or "cutout" (perforated)
    mode: str = "spline"              # "spline", "polygon", or "pixel"
    filter_speckle: int = 4           # Minimum area of speckle to discard (in pixels)
    color_precision: int = 7          # Significant bits for color quantization (1-8)
    layer_difference: int = 16        # Color difference threshold between layers (1-255)
    corner_threshold: int = 60        # Corner detection threshold in degrees (0-180)
    length_threshold: float = 4.0     # Minimum segment length threshold (pixels)
    max_iterations: int = 10          # Maximum iterations for curve fitting
    splice_threshold: int = 45        # Angle threshold for splicing curves (degrees)
    path_precision: int = 3           # Coordinate decimal precision in SVG output

    @classmethod
    def from_preset(
        cls,
        preset: Union[str, TracePreset] = TracePreset.LOGO,
        bw: bool = False,
        colors: Optional[int] = None,
    ) -> "TraceConfig":
        """Instantiate a TraceConfig using a preset name.

        Args:
            preset: Preset name ('logo', 'sharp', 'smooth').
            bw: If True, uses binary black & white mode.
            colors: Optional custom palette size to adjust color precision.

        Returns:
            Tuned TraceConfig instance.
        """
        if isinstance(preset, str):
            try:
                preset = TracePreset(preset.lower())
            except ValueError:
                preset = TracePreset.LOGO

        colormode = "binary" if bw else "color"

        if preset == TracePreset.SHARP:
            cfg = cls(
                colormode=colormode,
                hierarchical="stacked",
                mode="polygon",
                filter_speckle=3,
                color_precision=8,
                layer_difference=12,
                corner_threshold=30,
                length_threshold=3.0,
                max_iterations=12,
                splice_threshold=40,
                path_precision=3,
            )
        elif preset == TracePreset.SMOOTH:
            cfg = cls(
                colormode=colormode,
                hierarchical="stacked",
                mode="spline",
                filter_speckle=6,
                color_precision=6,
                layer_difference=18,
                corner_threshold=90,
                length_threshold=5.0,
                max_iterations=10,
                splice_threshold=50,
                path_precision=3,
            )
        else:  # TracePreset.LOGO
            cfg = cls(
                colormode=colormode,
                hierarchical="stacked",
                mode="spline",
                filter_speckle=4,
                color_precision=7,
                layer_difference=16,
                corner_threshold=60,
                length_threshold=4.0,
                max_iterations=10,
                splice_threshold=45,
                path_precision=3,
            )

        if colors is not None and colors > 0:
            # Map number of colors (1-8) to appropriate precision
            cfg.color_precision = max(4, min(8, colors))

        return cfg


def trace_image(
    image_input: Union[str, Path, Image.Image],
    output_path: Optional[Union[str, Path]] = None,
    preset: Union[str, TracePreset] = TracePreset.LOGO,
    bw: bool = False,
    colors: Optional[int] = None,
    config: Optional[TraceConfig] = None,
) -> str:
    """Trace a raster image into an SVG string and optionally write to output_path.

    Args:
        image_input: Path to raster image file or PIL Image instance.
        output_path: Optional file path to write SVG output to.
        preset: Preset mode ('logo', 'sharp', 'smooth').
        bw: Binary mode (black and white).
        colors: Optional number of quantized colors.
        config: Optional explicit TraceConfig overriding preset.

    Returns:
        The generated raw SVG string.

    Raises:
        TraceError: If vector tracing fails.
    """
    if config is None:
        config = TraceConfig.from_preset(preset=preset, bw=bw, colors=colors)

    temp_in = None
    temp_out = None

    try:
        # Prepare input file path for vtracer
        if isinstance(image_input, Image.Image):
            temp_in_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            temp_in = temp_in_file.name
            temp_in_file.close()
            image_input.save(temp_in, format="PNG")
            input_file_path = temp_in
        else:
            input_file_path = str(Path(image_input).resolve())
            if not os.path.isfile(input_file_path):
                raise FileNotFoundError(f"Input image file not found: {input_file_path}")

        # Prepare output file path
        if output_path is not None:
            resolved_out = Path(output_path).resolve()
            resolved_out.parent.mkdir(parents=True, exist_ok=True)
            target_out_path = str(resolved_out)
        else:
            temp_out_file = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
            temp_out = temp_out_file.name
            temp_out_file.close()
            target_out_path = temp_out

        # Invoke vtracer with positional parameters to ensure PyO3 compatibility
        try:
            vtracer.convert_image_to_svg_py(
                input_file_path,
                target_out_path,
                config.colormode,
                config.hierarchical,
                config.mode,
                int(config.filter_speckle),
                int(config.color_precision),
                int(config.layer_difference),
                int(config.corner_threshold),
                float(config.length_threshold),
                int(config.max_iterations),
                int(config.splice_threshold),
                int(config.path_precision),
            )
        except Exception as e:
            raise TraceError(f"vtracer conversion failed: {e}") from e

        # Read generated SVG
        try:
            with open(target_out_path, "r", encoding="utf-8") as f:
                svg_content = f.read()
        except Exception as e:
            raise TraceError(f"Failed to read generated SVG output: {e}") from e

        return svg_content

    finally:
        # Clean up temporary files
        if temp_in and os.path.exists(temp_in):
            try:
                os.remove(temp_in)
            except OSError:
                pass
        if temp_out and os.path.exists(temp_out):
            try:
                os.remove(temp_out)
            except OSError:
                pass
