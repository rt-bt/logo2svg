"""SVG optimization and post-processing module for logo2svg.

Ensures valid viewBox attributes for responsive vector scaling,
rounds path precision to minify file size, strips redundant attributes,
and verifies pure vector path output without embedded rasters.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Tuple, Union


class SvgOptimizationError(Exception):
    """Raised when an error occurs during SVG post-processing."""


# Regex to match floating point numbers in SVG path strings
FLOAT_REGEX = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")


def round_path_data(path_d: str, precision: int = 2) -> str:
    """Round floating-point coordinates in an SVG path 'd' attribute.

    Reduces SVG file size substantially while preserving visual accuracy.

    Args:
        path_d: The SVG path 'd' attribute string.
        precision: Decimal places to keep (default: 2).

    Returns:
        Optimized path 'd' string with rounded numbers.
    """
    def _replacer(match: re.Match) -> str:
        val_str = match.group(0)
        try:
            val = float(val_str)
            # Format to precision, strip trailing zeros and unnecessary dot
            formatted = f"{val:.{precision}f}".rstrip("0").rstrip(".")
            return "0" if formatted == "-0" or not formatted else formatted
        except ValueError:
            return val_str

    # Process all numeric tokens
    optimized = FLOAT_REGEX.sub(_replacer, path_d)
    # Collapse multiple spaces and trim
    return re.sub(r"\s+", " ", optimized).strip()


def extract_dimensions_from_svg(svg_content: str) -> Tuple[Optional[float], Optional[float]]:
    """Extract width and height attributes from root SVG tag.

    Args:
        svg_content: SVG string content.

    Returns:
        Tuple of (width, height) as floats, or (None, None) if not found.
    """
    # Quick regex matching on opening <svg ...> tag
    svg_match = re.search(r"<svg\b([^>]*)>", svg_content, re.IGNORECASE)
    if not svg_match:
        return None, None

    attrs_str = svg_match.group(1)
    w_match = re.search(r'\bwidth="([0-9.]+)(?:px)?"', attrs_str, re.IGNORECASE)
    h_match = re.search(r'\bheight="([0-9.]+)(?:px)?"', attrs_str, re.IGNORECASE)

    w = float(w_match.group(1)) if w_match else None
    h = float(h_match.group(1)) if h_match else None
    return w, h


def ensure_viewbox(
    svg_content: str,
    coord_width: Optional[float] = None,
    coord_height: Optional[float] = None,
    display_width: Optional[float] = None,
    display_height: Optional[float] = None,
) -> str:
    """Ensure the root SVG tag contains a valid viewBox matching the path coordinate system.

    A proper viewBox attribute allows the SVG to scale responsively and be edited
    in Inkscape, Illustrator, and web applications without clipping.

    Args:
        svg_content: SVG string content.
        coord_width: Coordinate space width for viewBox (defaults to extracted SVG width).
        coord_height: Coordinate space height for viewBox (defaults to extracted SVG height).
        display_width: Optional target display width for width attribute.
        display_height: Optional target display height for height attribute.

    Returns:
        Updated SVG string with viewBox ensured and optional display dimensions.
    """
    extracted_w, extracted_h = extract_dimensions_from_svg(svg_content)
    vw = coord_width if coord_width is not None else extracted_w
    vh = coord_height if coord_height is not None else extracted_h

    content = svg_content

    # If viewBox is not present, add it based on the coordinate space
    if not re.search(r'\bviewBox="[^"]*"', content, re.IGNORECASE) and vw is not None and vh is not None:
        vw_str = str(int(vw)) if vw.is_integer() else f"{vw:.2f}"
        vh_str = str(int(vh)) if vh.is_integer() else f"{vh:.2f}"
        viewbox_attr = f'viewBox="0 0 {vw_str} {vh_str}"'

        def _add_viewbox(match: re.Match) -> str:
            tag = match.group(0)
            return f"<svg {viewbox_attr}" + tag[4:]

        content = re.sub(r"<svg\b", _add_viewbox, content, count=1, flags=re.IGNORECASE)

    # If display dimensions specified, update width/height attributes
    if display_width is not None and display_height is not None:
        dw_str = str(int(display_width)) if display_width.is_integer() else f"{display_width:.2f}"
        dh_str = str(int(display_height)) if display_height.is_integer() else f"{display_height:.2f}"

        # Replace existing width/height
        content = re.sub(r'\bwidth="[0-9.]+(?:px)?"', f'width="{dw_str}"', content, count=1, flags=re.IGNORECASE)
        content = re.sub(r'\bheight="[0-9.]+(?:px)?"', f'height="{dh_str}"', content, count=1, flags=re.IGNORECASE)

    return content


def verify_pure_vector(svg_content: str) -> None:
    """Verify that the SVG contains pure vector paths and NO raster elements.

    Raises:
        SvgOptimizationError: If raster images or forbidden elements are present.
    """
    if re.search(r"<image\b", svg_content, re.IGNORECASE):
        raise SvgOptimizationError("SVG contains embedded <image> raster elements. Pure vector required.")

    if "data:image/" in svg_content:
        raise SvgOptimizationError("SVG contains base64 data:image URIs. Pure vector required.")

    if not re.search(r"<path\b", svg_content, re.IGNORECASE):
        raise SvgOptimizationError("SVG contains no vector <path> elements.")


def optimize_svg(
    svg_content: str,
    precision: int = 2,
    minify: bool = False,
    coord_width: Optional[float] = None,
    coord_height: Optional[float] = None,
    display_width: Optional[float] = None,
    display_height: Optional[float] = None,
    # Backward compatibility aliases
    width: Optional[float] = None,
    height: Optional[float] = None,
) -> str:
    """Optimize an SVG string for file size, standards compliance, and scalability.

    Steps:
    1. Ensure proper viewBox attribute on root <svg>.
    2. Strip redundant 'transform="translate(0,0)"' attributes.
    3. Round coordinate numbers in path 'd' attributes to reduce byte size.
    4. Clean unnecessary comments and redundant whitespace.
    5. Verify SVG consists of pure vector paths.

    Args:
        svg_content: Raw SVG input string.
        precision: Decimal places to round path numbers (default: 2).
        minify: If True, strips extra formatting whitespace into a single compact line.
        coord_width: Coordinate space width for viewBox.
        coord_height: Coordinate space height for viewBox.
        display_width: Target display width.
        display_height: Target display height.
        width: Deprecated alias for display_width or coord_width.
        height: Deprecated alias for display_height or coord_height.

    Returns:
        Optimized SVG string.
    """
    if not svg_content or not svg_content.strip():
        raise SvgOptimizationError("Empty SVG content received.")

    # 1. Ensure viewBox and display dimensions
    content = ensure_viewbox(
        svg_content,
        coord_width=coord_width,
        coord_height=coord_height,
        display_width=display_width if display_width is not None else width,
        display_height=display_height if display_height is not None else height,
    )

    # 2. Remove redundant translate(0,0) transforms produced by tracers
    content = re.sub(r'\s+transform="translate\(0\s*,\s*0\)"', "", content)

    # 3. Clean generator comment if desired
    content = re.sub(r"<!--\s*Generator:.*?-->\s*", "", content, flags=re.DOTALL)

    # 4. Optimize path data attributes
    def _optimize_path_d(match: re.Match) -> str:
        d_attr = match.group(1)
        optimized_d = round_path_data(d_attr, precision=precision)
        return f'd="{optimized_d}"'

    content = re.sub(r'\bd="([^"]*)"', _optimize_path_d, content)

    # 5. Verify pure vector elements
    verify_pure_vector(content)

    if minify:
        # Collapse multi-line whitespace
        content = re.sub(r"\s+", " ", content)
        content = re.sub(r">\s+<", "><", content).strip()
    else:
        # Standard clean multi-line formatting
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        content = "\n".join(lines)

    return content


def optimize_svg_file(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    precision: int = 2,
    minify: bool = False,
) -> str:
    """Read an SVG file, optimize its content, and save to output_file.

    Args:
        input_file: Path to source SVG.
        output_file: Path to output SVG (if None, overwrites input_file).
        precision: Coordinate rounding precision.
        minify: Whether to minify whitespace.

    Returns:
        Optimized SVG string.
    """
    in_path = Path(input_file).resolve()
    out_path = Path(output_file).resolve() if output_file else in_path

    with open(in_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    optimized = optimize_svg(svg_content, precision=precision, minify=minify)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(optimized)

    return optimized
