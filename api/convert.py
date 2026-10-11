"""Logo2SVG Vector Conversion API Endpoint.

Vercel serverless function dedicated to high-fidelity raster to SVG conversion.
"""

from __future__ import annotations

import base64
import io
import os
import re
import sys
import traceback
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request
from PIL import Image

app = Flask(__name__)
handler = app

# Ensure paths are configured for logo2svg imports
API_DIR = Path(__file__).resolve().parent
ROOT_DIR = API_DIR.parent

for p in [str(API_DIR), str(ROOT_DIR / "src"), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from logo2svg.converter import ConversionOptions, convert_image
    from logo2svg.trace import TracePreset
except Exception:
    try:
        from api.logo2svg.converter import ConversionOptions, convert_image
        from api.logo2svg.trace import TracePreset
    except Exception:
        convert_image = None
        ConversionOptions = None


def extract_svg_stats(svg_content: str) -> dict:
    """Extract path count and color swatches from SVG string."""
    path_count = len(re.findall(r"<path\b", svg_content, re.IGNORECASE))
    hex_colors = set(re.findall(r'fill="([#A-Fa-f0-9]{6,8})"', svg_content))
    unique_colors = sorted(list(hex_colors))[:16]
    return {
        "path_count": path_count,
        "colors": unique_colors,
    }


def image_to_data_url(img: Image.Image) -> str:
    """Convert PIL image to PNG Base64 Data URL safely across all modes."""
    img_conv = img
    if img_conv.mode == "CMYK":
        img_conv = img_conv.convert("RGB")
    elif img_conv.mode not in ("RGB", "RGBA", "L"):
        img_conv = img_conv.convert("RGBA")
    buffered = io.BytesIO()
    img_conv.save(buffered, format="PNG")
    b64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


def find_sample_file(sample_name: str) -> Optional[Path]:
    """Find a sample file across possible deployment locations."""
    candidates = [
        API_DIR / "examples" / sample_name,
        ROOT_DIR / "public" / "examples" / sample_name,
        ROOT_DIR / "examples" / sample_name,
        Path("/var/task/api/examples") / sample_name,
        Path("/var/task/public/examples") / sample_name,
        Path("/var/task/examples") / sample_name,
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@app.route("/", methods=["GET", "POST", "OPTIONS"], strict_slashes=False)
@app.route("/api/convert", methods=["GET", "POST", "OPTIONS"], strict_slashes=False)
def handle_convert():
    if request.method == "OPTIONS":
        return "", 204

    if request.method == "GET":
        return jsonify({
            "status": "ready",
            "endpoint": "/api/convert",
            "method": "POST",
            "engine": "vtracer + logo2svg",
        })

    try:
        if convert_image is None or ConversionOptions is None:
            return jsonify({
                "success": False,
                "error": "Conversion engine module failed to load",
            }), 500

        input_img: Optional[Image.Image] = None
        orig_bytes = 0
        input_filename = "logo"

        if "file" in request.files and request.files["file"].filename:
            f = request.files["file"]
            raw_data = f.read()
            orig_bytes = len(raw_data)
            input_img = Image.open(io.BytesIO(raw_data))
            input_filename = Path(f.filename).stem
        elif "sample" in request.form and request.form["sample"]:
            sample_name = request.form["sample"]
            sample_path = find_sample_file(sample_name)
            if not sample_path:
                return jsonify({"error": f"Sample not found: {sample_name}"}), 400
            orig_bytes = sample_path.stat().st_size
            input_img = Image.open(sample_path)
            input_filename = sample_path.stem
        elif request.is_json and request.json and "sample" in request.json:
            sample_name = request.json["sample"]
            sample_path = find_sample_file(sample_name)
            if not sample_path:
                return jsonify({"error": f"Sample not found: {sample_name}"}), 400
            orig_bytes = sample_path.stat().st_size
            input_img = Image.open(sample_path)
            input_filename = sample_path.stem
        else:
            return jsonify({"error": "No image uploaded or sample selected"}), 400

        params = request.form if request.form else (request.json or {})

        preset = params.get("preset", "logo").lower()
        if preset not in ["logo", "sharp", "smooth"]:
            preset = "logo"

        bw = str(params.get("bw", "false")).lower() in ("true", "1", "yes")
        keep_alpha = str(params.get("keep_alpha", "false")).lower() in ("true", "1", "yes")
        denoise = str(params.get("denoise", "false")).lower() in ("true", "1", "yes")
        minify = str(params.get("minify", "false")).lower() in ("true", "1", "yes")

        colors_val = params.get("colors")
        colors = None
        if colors_val is not None and str(colors_val).strip() != "" and str(colors_val).isdigit():
            colors = int(colors_val)

        scale_val = params.get("scale")
        scale = None
        if scale_val is not None and str(scale_val).strip() != "":
            try:
                scale = float(scale_val)
            except ValueError:
                scale = None

        precision_val = params.get("precision", "2")
        try:
            precision = int(precision_val)
        except ValueError:
            precision = 2

        options = ConversionOptions(
            preset=preset,
            bw=bw,
            colors=colors,
            scale=scale,
            keep_alpha=keep_alpha,
            denoise=denoise,
            precision=precision,
            minify=minify,
            optimize=True,
            check_quality=True,
        )

        result = convert_image(input_path=input_img, options=options)
        stats = extract_svg_stats(result.svg_content)
        data_url = image_to_data_url(input_img)

        ssim_val = result.comparison.similarity_percentage if result.comparison else 0.0
        psnr_val = result.comparison.psnr if result.comparison else 0.0
        if psnr_val == float("inf"):
            psnr_display = "Infinity (Lossless)"
        else:
            psnr_display = f"{psnr_val:.2f} dB"

        return jsonify({
            "success": True,
            "filename": input_filename,
            "svg_content": result.svg_content,
            "svg_size_bytes": result.svg_size_bytes,
            "original_size_bytes": orig_bytes or result.original_size_bytes,
            "original_dimensions": [input_img.width, input_img.height],
            "original_data_url": data_url,
            "ssim_percentage": round(ssim_val, 2),
            "psnr_display": psnr_display,
            "path_count": stats["path_count"],
            "colors": stats["colors"],
            "options": {
                "preset": preset,
                "bw": bw,
                "colors": colors,
                "scale": scale,
                "keep_alpha": keep_alpha,
                "denoise": denoise,
                "precision": precision,
                "minify": minify,
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500
