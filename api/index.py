"""Logo2SVG Creative Studio - Vercel Serverless Function & REST API.

Self-contained WSGI Flask application serving the conversion engine,
sample logo catalog, and vector synthesis pipeline.
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

from flask import Flask, jsonify, request, send_file, send_from_directory
from PIL import Image

init_error = None

try:
    API_DIR = Path(__file__).resolve().parent
    if str(API_DIR) not in sys.path:
        sys.path.insert(0, str(API_DIR))

    ROOT_DIR = API_DIR.parent
    if str(ROOT_DIR / "src") not in sys.path:
        sys.path.insert(0, str(ROOT_DIR / "src"))

    PUBLIC_DIR = ROOT_DIR / "public"

    # Try importing logo2svg
    try:
        from logo2svg.converter import ConversionOptions, convert_image
        from logo2svg.trace import TracePreset
    except ImportError:
        from api.logo2svg.converter import ConversionOptions, convert_image
        from api.logo2svg.trace import TracePreset

    # Determine sample logos directory
    EXAMPLES_DIR = API_DIR / "examples"
    if not EXAMPLES_DIR.is_dir():
        EXAMPLES_DIR = ROOT_DIR / "examples"

    app = Flask(__name__, static_folder=str(PUBLIC_DIR), static_url_path="")

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

    @app.route("/")
    def index():
        """Serve homepage as fallback if requested directly from lambda."""
        if PUBLIC_DIR.is_dir() and (PUBLIC_DIR / "index.html").is_file():
            return send_from_directory(str(PUBLIC_DIR), "index.html")
        web_dir = ROOT_DIR / "web"
        if web_dir.is_dir() and (web_dir / "index.html").is_file():
            return send_from_directory(str(web_dir), "index.html")
        return "Logo2SVG Studio API is running."

    @app.route("/api/samples", methods=["GET"])
    def get_samples():
        """Return available sample logos with metadata."""
        sample_list = []
        sample_meta = {
            "geometric_logo": {"title": "Geometric Mark", "category": "Geometric", "desc": "Clean shapes & angles"},
            "tech_shield": {"title": "Tech Shield", "category": "Icon", "desc": "Sharp modern cybersecurity badge"},
            "smooth_badge": {"title": "Smooth Badge", "category": "Badge", "desc": "Curved gradients & borders"},
            "transparent_icon": {"title": "Alpha Icon", "category": "Transparent", "desc": "Transparent PNG mark"},
            "retro_crest": {"title": "Retro Crest", "category": "Vintage", "desc": "Detailed vintage emblem"},
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
            file_path = PUBLIC_DIR / "examples" / filename
        if not file_path.is_file():
            return jsonify({"error": "File not found"}), 404
        return send_file(str(file_path))

    @app.route("/api/convert", methods=["POST"])
    def convert():
        """Execute vector conversion pipeline."""
        try:
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
                    sample_path = PUBLIC_DIR / "examples" / sample_name
                if not sample_path.is_file():
                    return jsonify({"error": f"Sample not found: {sample_name}"}), 400
                orig_bytes = sample_path.stat().st_size
                input_img = Image.open(sample_path)
                input_filename = sample_path.stem
            elif request.is_json and request.json and "sample" in request.json:
                sample_name = request.json["sample"]
                sample_path = EXAMPLES_DIR / sample_name
                if not sample_path.is_file():
                    sample_path = PUBLIC_DIR / "examples" / sample_name
                if not sample_path.is_file():
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
            return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500

    @app.route("/<path:path>")
    def static_proxy(path: str):
        """Serve static files if requested through Flask."""
        if PUBLIC_DIR.is_dir() and (PUBLIC_DIR / path).is_file():
            return send_from_directory(str(PUBLIC_DIR), path)
        return jsonify({"error": "Not found"}), 404

except Exception as ex:
    init_error = traceback.format_exc()
    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def error_fallback(path: str):
        return jsonify({
            "error": "Serverless Initialization Failed",
            "message": str(ex),
            "traceback": init_error,
        }), 500
