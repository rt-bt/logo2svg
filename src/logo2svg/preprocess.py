"""Image preprocessing pipeline for logo2svg.

Handles validation, transparency flattening, auto-upscaling (LANCZOS),
median filter denoising for JPG artifacts, and color quantization.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image, ImageFilter, ImageOps

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


class PreprocessError(Exception):
    """Raised when an error occurs during image preprocessing."""


class UnsupportedFormatError(PreprocessError):
    """Raised when the input image format is not supported."""


class CorruptedImageError(PreprocessError):
    """Raised when the input image cannot be read or is corrupted."""


@dataclass
class PreprocessResult:
    """Encapsulates the output and metadata of the preprocessing pipeline."""

    image: Image.Image
    original_size: Tuple[int, int]  # (width, height)
    final_size: Tuple[int, int]  # (width, height)
    scale_factor: float
    has_alpha: bool
    format: str


def validate_image_path(image_path: Union[str, Path]) -> Path:
    """Validate that the image path exists and has a supported extension.

    Args:
        image_path: Path to the input image file.

    Returns:
        Resolved Path object.

    Raises:
        FileNotFoundError: If the file does not exist.
        UnsupportedFormatError: If the file extension is not supported.
    """
    path = Path(image_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Input image not found: {path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFormatError(
            f"Unsupported image format '{ext}'. Supported formats: "
            f"{', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    return path


def load_image(image_input: Union[str, Path, Image.Image]) -> Tuple[Image.Image, str]:
    """Load and verify an image from a path or return an existing PIL Image.

    Args:
        image_input: File path or PIL Image instance.

    Returns:
        Tuple of (PIL Image in memory, format name).

    Raises:
        FileNotFoundError: If file path does not exist.
        UnsupportedFormatError: If format is unsupported.
        CorruptedImageError: If image file is corrupted or unreadable.
    """
    if isinstance(image_input, Image.Image):
        # Already an image in memory
        fmt = (image_input.format or "PNG").upper()
        return image_input.copy(), fmt

    path = validate_image_path(image_input)

    try:
        with Image.open(path) as img:
            img.verify()
    except Exception as e:
        raise CorruptedImageError(f"Corrupted or invalid image at {path}: {e}") from e

    try:
        # Re-open after verify() closes/invalidates the file handle
        with Image.open(path) as img:
            fmt = (img.format or path.suffix.lstrip(".").upper())
            # Load pixel data into memory so file handle can close safely
            img_copy = img.copy()
            return img_copy, fmt
    except Exception as e:
        raise CorruptedImageError(f"Failed to load image at {path}: {e}") from e


def flatten_transparency(image: Image.Image, background_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """Flatten an image with an alpha channel onto a solid background.

    Args:
        image: Source PIL image.
        background_color: RGB tuple for the background (default: white).

    Returns:
        RGB PIL image with transparency flattened onto the specified background.
    """
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (*background_color, 255))
        # Alpha composite creates a smooth blend
        composited = Image.alpha_composite(background, rgba)
        return composited.convert("RGB")
    return image.convert("RGB")


def auto_upscale(
    image: Image.Image,
    target_min_dim: int = 1000,
    default_multiplier: float = 2.0,
    user_scale: Optional[float] = None,
) -> Tuple[Image.Image, float]:
    """Upscale image using high-quality LANCZOS resampling if below target dimension.

    Vector tracing works substantially better with higher resolution inputs,
    preventing blocky staircasing on curved logos.

    Args:
        image: Source PIL image.
        target_min_dim: Minimum dimension below which auto-upscaling triggers.
        default_multiplier: Scale factor when auto-upscaling (default: 2.0x).
        user_scale: Explicit scale factor if specified by user.

    Returns:
        Tuple of (upscaled PIL image, effective scale factor).
    """
    w, h = image.size

    if user_scale is not None and user_scale > 0:
        multiplier = float(user_scale)
    elif w < target_min_dim or h < target_min_dim:
        multiplier = default_multiplier
    else:
        multiplier = 1.0

    if multiplier == 1.0:
        return image, 1.0

    new_w = max(1, int(round(w * multiplier)))
    new_h = max(1, int(round(h * multiplier)))

    # Use LANCZOS (formerly ANTIALIAS) for high-fidelity resizing
    upscaled = image.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
    return upscaled, multiplier


def denoise_image(image: Image.Image, filter_size: int = 3) -> Image.Image:
    """Apply median filter denoising to reduce compression artifacts and noise.

    Especially effective for JPG/JPEG logos that suffer from edge ringing
    and 8x8 block compression artifacts.

    Args:
        image: Source PIL image.
        filter_size: Aperture linear size; must be odd (default: 3).

    Returns:
        Denoised PIL image.
    """
    if filter_size <= 1:
        return image
    return image.filter(ImageFilter.MedianFilter(size=filter_size))


def quantize_colors(image: Image.Image, num_colors: int) -> Image.Image:
    """Quantize image to a specified number of colors (1-8 or more).

    Reduces color gradients and sensor noise, producing clean, solid color
    regions optimal for logo vectorization.

    Args:
        image: Source PIL image.
        num_colors: Target number of colors (typically 1-8).

    Returns:
        Quantized RGB or RGBA PIL image.
    """
    if num_colors <= 0:
        return image

    num_colors = max(1, min(256, num_colors))

    # Keep track of alpha if present
    alpha = None
    if image.mode == "RGBA":
        alpha = image.split()[3]
        rgb = image.convert("RGB")
    else:
        rgb = image.convert("RGB")

    # Quantize using median cut
    quantized_p = rgb.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    quantized_rgb = quantized_p.convert("RGB")

    if alpha is not None:
        quantized_rgb.putalpha(alpha)
        return quantized_rgb

    return quantized_rgb


def binarize_image(image: Image.Image, threshold: Optional[int] = None) -> Image.Image:
    """Convert an image to crisp binary black-and-white.

    If threshold is None, computes Otsu's threshold automatically for optimal separation.

    Args:
        image: Source PIL image.
        threshold: Luminance threshold (0-255) or None for automatic thresholding.

    Returns:
        Binary 'L' mode PIL image with values strictly 0 or 255.
    """
    gray = image.convert("L")

    if threshold is None:
        # Otsu thresholding via histogram
        hist = gray.histogram()
        total = sum(hist)
        sum_total = sum(i * hist[i] for i in range(256))

        sum_b = 0
        w_b = 0
        maximum = 0.0
        best_thresh = 128

        for i in range(256):
            w_b += hist[i]
            if w_b == 0:
                continue
            w_f = total - w_b
            if w_f == 0:
                break

            sum_b += i * hist[i]
            m_b = sum_b / w_b
            m_f = (sum_total - sum_b) / w_f

            between_variance = w_b * w_f * ((m_b - m_f) ** 2)
            if between_variance > maximum:
                maximum = between_variance
                best_thresh = i

        threshold = best_thresh

    # Point transform: >= threshold -> 255, < threshold -> 0
    table = [0 if i < threshold else 255 for i in range(256)]
    return gray.point(table, mode="L")


def preprocess_image(
    image_input: Union[str, Path, Image.Image],
    keep_alpha: bool = False,
    scale: Optional[float] = None,
    denoise: bool = False,
    colors: Optional[int] = None,
    bw: bool = False,
) -> PreprocessResult:
    """Execute the full preprocessing pipeline on an image.

    Pipeline steps:
    1. Load and validate image integrity.
    2. Check and handle alpha channel (flatten to white unless keep_alpha).
    3. Auto-upscale small images (<1000px) 2x using LANCZOS or custom scale.
    4. Apply median filter denoise if requested or if JPG with artifacts.
    5. Apply binarization (if bw=True) or color quantization (if colors specified).

    Args:
        image_input: File path or PIL Image.
        keep_alpha: If True, preserves transparency; otherwise flattens to white.
        scale: Custom upscale multiplier (e.g. 2.0). If None, auto-upscales if <1000px.
        denoise: If True, applies a median filter to remove JPG/compression noise.
        colors: Optional number of colors for quantization (1-8).
        bw: If True, converts image to pure black & white.

    Returns:
        PreprocessResult containing the processed image and metadata.
    """
    img, fmt = load_image(image_input)
    orig_size = img.size
    has_alpha = (img.mode in ("RGBA", "LA")) or (img.mode == "P" and "transparency" in img.info)

    # 1. Flatten transparency unless keep_alpha requested
    if not keep_alpha:
        img = flatten_transparency(img)
    else:
        if img.mode != "RGBA":
            img = img.convert("RGBA")

    # 2. Auto-upscale using Lanczos
    img, effective_scale = auto_upscale(img, target_min_dim=1000, default_multiplier=2.0, user_scale=scale)

    # 3. Denoise if requested or if JPEG format
    if denoise or fmt.upper() in ("JPEG", "JPG"):
        img = denoise_image(img, filter_size=3)

    # 4. Color reduction / binary mode
    if bw:
        img = binarize_image(img)
        # Convert back to RGB for consistency in downstream tracers
        img = img.convert("RGB")
    elif colors is not None and colors > 0:
        img = quantize_colors(img, num_colors=colors)

    return PreprocessResult(
        image=img,
        original_size=orig_size,
        final_size=img.size,
        scale_factor=effective_scale,
        has_alpha=has_alpha and keep_alpha,
        format=fmt,
    )
