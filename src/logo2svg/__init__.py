"""logo2svg - Production-quality raster logo to SVG vector converter.

Converts raster logos (PNG, JPG, WEBP, BMP) into clean, accurate,
scalable SVG vector files matching the original logo as closely as possible.
"""

from .compare import ComparisonResult, compare_svg_to_image, render_svg_to_image
from .converter import ConversionOptions, ConversionResult, convert_image
from .optimize import optimize_svg
from .preprocess import PreprocessResult, preprocess_image
from .trace import TracePreset, trace_image

__version__ = "1.0.0"
__all__ = [
    "__version__",
    "convert_image",
    "ConversionOptions",
    "ConversionResult",
    "preprocess_image",
    "PreprocessResult",
    "trace_image",
    "TracePreset",
    "optimize_svg",
    "compare_svg_to_image",
    "render_svg_to_image",
    "ComparisonResult",
]
