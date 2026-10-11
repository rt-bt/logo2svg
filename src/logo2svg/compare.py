"""Quality verification and comparison module for logo2svg.

Renders vector SVG files back into raster PNG images using cairosvg
(with automatic resvg-py fallback on environments lacking libcairo),
and computes Structural Similarity Index (SSIM) against the original logo.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as compute_ssim


class RenderingError(Exception):
    """Raised when an error occurs during SVG rasterization."""


@dataclass
class ComparisonResult:
    """Encapsulates the quality comparison between original and vector output."""

    ssim: float                      # Structural Similarity Index (0.0 to 1.0)
    similarity_percentage: float     # SSIM expressed as percentage (0 - 100%)
    psnr: float                      # Peak Signal-to-Noise Ratio (dB)
    renderer: str                    # Name of the rasterizer backend used
    rendered_image: Image.Image      # The re-rendered PIL Image

    def __str__(self) -> str:
        return (
            f"Quality Score: {self.similarity_percentage:.2f}% visual match "
            f"(SSIM: {self.ssim:.4f}, PSNR: {self.psnr:.2f} dB, Renderer: {self.renderer})"
        )


def render_svg_to_image(
    svg_content: Union[str, bytes],
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
) -> Tuple[Image.Image, str]:
    """Render an SVG string or bytes to a PIL Image.

    Attempts rendering via cairosvg first; if Cairo dynamic libraries are unavailable
    (e.g., on Windows without GTK/Cairo DLLs), gracefully falls back to resvg-py.

    Args:
        svg_content: SVG content as string or bytes.
        target_width: Desired output image width.
        target_height: Desired output image height.

    Returns:
        Tuple of (rendered PIL Image in RGBA, renderer_name).

    Raises:
        RenderingError: If neither cairosvg nor resvg-py can render the SVG.
    """
    svg_bytes = svg_content.encode("utf-8") if isinstance(svg_content, str) else svg_content
    svg_str = svg_content if isinstance(svg_content, str) else svg_content.decode("utf-8", errors="ignore")

    # Method 1: Try cairosvg
    try:
        import cairosvg
        kwargs = {"bytestring": svg_bytes}
        if target_width:
            kwargs["output_width"] = target_width
        if target_height:
            kwargs["output_height"] = target_height

        png_data = cairosvg.svg2png(**kwargs)
        if png_data:
            img = Image.open(io.BytesIO(png_data)).convert("RGBA")
            return img, "cairosvg"
    except (ImportError, OSError, Exception):
        # cairosvg failed or libcairo-2.dll not present -> fallback
        pass

    # Method 2: Fallback to resvg-py
    try:
        import resvg_py

        # resvg_py renders directly from SVG string
        png_data = resvg_py.svg_to_bytes(svg_str)
        if png_data:
            img = Image.open(io.BytesIO(png_data)).convert("RGBA")
            if target_width and target_height and img.size != (target_width, target_height):
                img = img.resize((target_width, target_height), resample=Image.Resampling.LANCZOS)
            return img, "resvg"
    except (ImportError, Exception) as e:
        raise RenderingError(
            f"Failed to render SVG using both cairosvg and resvg-py: {e}"
        ) from e

    raise RenderingError("No working SVG renderer could produce image data.")


def calculate_psnr(image_a: np.ndarray, image_b: np.ndarray) -> float:
    """Calculate Peak Signal-to-Noise Ratio (PSNR) in dB between two images.

    Args:
        image_a: First image array (uint8).
        image_b: Second image array (uint8).

    Returns:
        PSNR value in decibels (dB), or float('inf') if images are identical.
    """
    mse = np.mean((image_a.astype(np.float64) - image_b.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return float(20 * math.log10(255.0 / math.sqrt(mse)))


def compare_svg_to_image(
    svg_input: Union[str, Path, bytes],
    reference_image: Union[str, Path, Image.Image],
) -> ComparisonResult:
    """Compare an SVG vector file against a reference raster logo using SSIM.

    Args:
        svg_input: SVG file path, SVG content string, or bytes.
        reference_image: File path or PIL Image instance of the original logo.

    Returns:
        ComparisonResult containing SSIM, PSNR, and rendered image.
    """
    # 1. Load reference image
    if isinstance(reference_image, (str, Path)):
        ref_img = Image.open(reference_image).convert("RGBA")
    else:
        ref_img = reference_image.convert("RGBA")

    # 2. Load SVG content
    if isinstance(svg_input, (str, Path)) and (
        isinstance(svg_input, Path) or (isinstance(svg_input, str) and not svg_input.strip().startswith("<"))
    ):
        svg_path = Path(svg_input)
        if svg_path.is_file():
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_content = f.read()
        else:
            svg_content = str(svg_input)
    else:
        svg_content = svg_input.decode("utf-8") if isinstance(svg_input, bytes) else str(svg_input)

    # 3. Render SVG at reference image resolution
    rendered_img, renderer_name = render_svg_to_image(
        svg_content=svg_content,
        target_width=ref_img.width,
        target_height=ref_img.height,
    )

    # Ensure rendered image matches reference dimensions
    if rendered_img.size != ref_img.size:
        rendered_img = rendered_img.resize(ref_img.size, resample=Image.Resampling.LANCZOS)

    # 4. Flatten transparent areas to white for fair visual comparison
    ref_rgb = Image.new("RGB", ref_img.size, (255, 255, 255))
    ref_rgb.paste(ref_img, mask=ref_img.split()[3])

    rend_rgb = Image.new("RGB", rendered_img.size, (255, 255, 255))
    rend_rgb.paste(rendered_img, mask=rendered_img.split()[3])

    # Convert to grayscale numpy arrays for SSIM calculation
    ref_gray = np.array(ref_rgb.convert("L"))
    rend_gray = np.array(rend_rgb.convert("L"))

    # 5. Compute SSIM
    ssim_val = float(compute_ssim(ref_gray, rend_gray, data_range=255))
    # Bound SSIM safely between 0.0 and 1.0
    ssim_val = max(0.0, min(1.0, ssim_val))

    # 6. Compute PSNR
    psnr_val = calculate_psnr(ref_gray, rend_gray)

    return ComparisonResult(
        ssim=ssim_val,
        similarity_percentage=ssim_val * 100.0,
        psnr=psnr_val,
        renderer=renderer_name,
        rendered_image=rendered_img,
    )
