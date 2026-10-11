"""Logo2SVG Creative Studio - Standalone Web Server.

High-performance Flask server serving the modern HTML5/CSS/JavaScript
Creative Studio frontend and REST API for raster-to-vector conversion.
"""

from __future__ import annotations

import argparse
import base64
import io
import os
import re
import socket
import sys
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, jsonify, request, send_file, send_from_directory
from PIL import Image

# Ensure src directory is in path
SRC_DIR = Path(__file__).resolve().parent / "src"
if SRC_DIR.is_dir() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from logo2svg.converter import ConversionOptions, convert_image
from logo2svg.preprocess import SUPPORTED_EXTENSIONS
from logo2svg.trace import TracePreset

ROOT_DIR = Path(__file__).resolve().parent
WEB_DIR = ROOT_DIR / "web"
EXAMPLES_DIR = ROOT_DIR / "examples"

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")


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
    """Convert PIL image to PNG Base64 Data URL."""
    img_conv = img
    if img_conv.mode == "CMYK":
        img_conv = img_conv.convert("RGB")
    elif img_conv.mode not in ("RGB", "RGBA", "L"):
        img_conv = img_conv.convert("RGBA")
    buffered = io.BytesIO()
    img_conv.save(buffered, format="PNG")
    b64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


def find_free_port(start_port: int = 5000) -> int:
    """Find an available TCP port starting from start_port."""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


@app.route("/")
def index():
    """Serve main Creative Studio application."""
    return send_from_directory(str(WEB_DIR), "index.html")


@app.route("/api/samples", methods=["GET"])
def get_samples():
    """Return available sample logos with metadata."""
    sample_list = []
    sample_meta = {
        "geometric_logo": {"title": "Geometric Mark", "category": "Geometric", "desc": "Clean shapes & angles"},
        "retro_crest": {"title": "Retro Crest", "category": "Vintage", "desc": "Detailed vintage emblem"},
        "smooth_badge": {"title": "Smooth Badge", "category": "Badge", "desc": "Curved gradients & borders"},
        "tech_shield": {"title": "Tech Shield", "category": "Icon", "desc": "Sharp modern cybersecurity badge"},
        "transparent_icon": {"title": "Alpha Icon", "category": "Transparent", "desc": "Transparent PNG mark"},
    }

    if EXAMPLES_DIR.is_dir():
        for ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
            for p in sorted(EXAMPLES_DIR.glob(f"*{ext}")):
                stem = p.stem
                meta = sample_meta.get(stem, {
                    "title": stem.replace("_", " ").title(),
                    "category": "Sample",
                    "desc": f"Raster format {ext.upper()}",
                })
                sample_list.append({
                    "id": stem,
                    "filename": p.name,
                    "title": meta["title"],
                    "category": meta["category"],
                    "description": meta["desc"],
                    "url": f"/api/sample/{p.name}",
                    "size_bytes": p.stat().st_size,
                })
    return jsonify({"samples": sample_list})


@app.route("/api/sample/<filename>", methods=["GET"])
def get_sample_file(filename: str):
    """Serve a sample image from examples/."""
    file_path = EXAMPLES_DIR / filename
    if not file_path.is_file():
        return jsonify({"error": "File not found"}), 404
    return send_file(str(file_path))


@app.route("/api/convert", methods=["POST"])
def convert():
    """Execute vector conversion pipeline."""
    try:
        # Determine image input: either uploaded file or sample filename
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
            sample_path = EXAMPLES_DIR / sample_name
            if not sample_path.is_file():
                return jsonify({"error": f"Sample not found: {sample_name}"}), 400
            orig_bytes = sample_path.stat().st_size
            input_img = Image.open(sample_path)
            input_filename = sample_path.stem
        elif request.is_json and request.json and "sample" in request.json:
            sample_name = request.json["sample"]
            sample_path = EXAMPLES_DIR / sample_name
            if not sample_path.is_file():
                return jsonify({"error": f"Sample not found: {sample_name}"}), 400
            orig_bytes = sample_path.stat().st_size
            input_img = Image.open(sample_path)
            input_filename = sample_path.stem
        else:
            return jsonify({"error": "No image uploaded or sample selected"}), 400

        # Parse tuning options
        params = request.form if request.form else (request.json or {})

        preset = params.get("preset", "logo").lower()
        if preset not in ["logo", "sharp", "smooth"]:
            preset = "logo"

        bw = str(params.get("bw", "false")).lower() in ("true", "1", "yes")
        keep_alpha = str(params.get("keep_alpha", "false")).lower() in ("true", "1", "yes")
        denoise = str(params.get("denoise", "false")).lower() in ("true", "1", "yes")
        minify = str(params.get("minify", "false")).lower() in ("true", "1", "yes")
        
        # Colors
        colors_val = params.get("colors")
        colors = None
        if colors_val is not None and str(colors_val).strip() != "" and str(colors_val).isdigit():
            colors = int(colors_val)

        # Scale
        scale_val = params.get("scale")
        scale = None
        if scale_val is not None and str(scale_val).strip() != "":
            try:
                scale = float(scale_val)
            except ValueError:
                scale = None

        # Precision
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

        # Execute conversion
        result = convert_image(input_path=input_img, options=options)

        # Extract stats
        stats = extract_svg_stats(result.svg_content)
        data_url = image_to_data_url(input_img)

        # SSIM and PSNR
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
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


def run_server(port: Optional[int] = None, host: str = "127.0.0.1", open_browser: bool = True):
    """Start web studio server."""
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

    actual_port = port if port else find_free_port(5000)
    url = f"http://{host}:{actual_port}"
    print("=" * 65)
    print("  Logo2SVG Creative Studio - High Fidelity Vector Engine")
    print(f"  Running at: {url}")
    print(f"  Web assets: {WEB_DIR}")
    print("=" * 65)

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    app.run(host=host, port=actual_port, debug=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Logo2SVG Creative Studio Web Server")
    parser.add_argument("--port", type=int, default=None, help="TCP port (default: auto find starting at 5000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")
    args = parser.parse_args()

    run_server(port=args.port, host=args.host, open_browser=not args.no_browser)
