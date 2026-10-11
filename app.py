"""Streamlit Web UI for logo2svg.

Features:
- Drag-and-drop upload for PNG, JPG, WEBP, BMP logos.
- Quick-select sample logos from examples directory.
- Preset selector ('logo', 'sharp', 'smooth') with parameter controls.
- Side-by-side original vs vector SVG preview.
- Quality score badge (SSIM similarity percentage).
- One-click SVG download button.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Optional

import streamlit as st
from PIL import Image

# Ensure src directory is in path
src_path = Path(__file__).resolve().parent / "src"
if src_path.is_dir() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from logo2svg.converter import ConversionOptions, convert_image
from logo2svg.preprocess import SUPPORTED_EXTENSIONS
from logo2svg.trace import TracePreset

# Configure Streamlit page
st.set_page_config(
    page_title="logo2svg - Raster Logo to Scalable Vector Graphics",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)


def format_bytes(b: int) -> str:
    """Format bytes into human-readable string."""
    if b < 1024:
        return f"{b} B"
    elif b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    else:
        return f"{b / (1024 * 1024):.2f} MB"


def get_sample_logos() -> dict[str, Path]:
    """Retrieve available sample logos from examples/ directory."""
    examples_dir = Path(__file__).resolve().parent / "examples"
    samples = {}
    if examples_dir.is_dir():
        for ext in SUPPORTED_EXTENSIONS:
            for p in sorted(examples_dir.glob(f"*{ext}")):
                samples[p.name] = p
    return samples


def main() -> None:
    # Sidebar
    st.sidebar.title("⚙️ Conversion Settings")

    preset_name = st.sidebar.selectbox(
        "Tracing Preset",
        options=["logo", "sharp", "smooth"],
        index=0,
        help=(
            "• logo: Balanced Bézier curves (best for typical logos)\n"
            "• sharp: Polygon mode (best for geometric/tech logos)\n"
            "• smooth: Fluid curves (best for badges & organic shapes)"
        ),
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Preprocessing Options")

    bw_mode = st.sidebar.checkbox(
        "Black & White Mode (--bw)",
        value=False,
        help="Binarize logo to pure black and white vectors.",
    )

    keep_alpha = st.sidebar.checkbox(
        "Keep Alpha Transparency (--keep-alpha)",
        value=False,
        help="Preserve transparency instead of flattening onto a solid white background.",
    )

    denoise = st.sidebar.checkbox(
        "Median Denoise (--denoise)",
        value=False,
        help="Apply median filter to remove JPG compression ringing and artifacts.",
    )

    quantize_colors = st.sidebar.checkbox("Color Quantization (--colors)", value=False)
    num_colors = None
    if quantize_colors:
        num_colors = st.sidebar.slider("Number of Colors", min_value=1, max_value=8, value=4)

    scale_choice = st.sidebar.selectbox(
        "Scale Factor (--scale)",
        options=["Auto (2x for <1000px)", "1.0x (Original)", "2.0x (High-Res)", "3.0x", "4.0x"],
        index=0,
    )

    scale_val: Optional[float] = None
    if "1.0x" in scale_choice:
        scale_val = 1.0
    elif "2.0x" in scale_choice:
        scale_val = 2.0
    elif "3.0x" in scale_choice:
        scale_val = 3.0
    elif "4.0x" in scale_choice:
        scale_val = 4.0

    st.sidebar.markdown("---")
    st.sidebar.subheader("Post-Processing & Optimization")

    precision = st.sidebar.slider(
        "Path Decimal Precision",
        min_value=1,
        max_value=4,
        value=2,
        help="Number of decimal digits for coordinates in SVG path elements.",
    )

    minify = st.sidebar.checkbox("Minify SVG", value=False)

    # Main content
    st.title("🎨 logo2svg")
    st.markdown(
        "Convert raster logos (**PNG, JPG, WEBP, BMP**) into clean, accurate, "
        "scalable **SVG vector files** editable in Inkscape and Illustrator."
    )

    # Input Selection tabs
    sample_logos = get_sample_logos()
    tab_upload, tab_sample = st.tabs(["📤 Upload Image", "🖼️ Try Sample Logos"])

    input_img: Optional[Image.Image] = None
    input_filename = "logo"
    orig_bytes = 0

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Choose a logo file",
            type=["png", "jpg", "jpeg", "webp", "bmp"],
            help="Drag and drop or browse for a raster image.",
        )
        if uploaded_file is not None:
            raw_bytes = uploaded_file.read()
            orig_bytes = len(raw_bytes)
            input_img = Image.open(io.BytesIO(raw_bytes))
            input_filename = Path(uploaded_file.name).stem

    with tab_sample:
        if sample_logos:
            sample_choice = st.selectbox("Choose a sample logo:", list(sample_logos.keys()))
            if sample_choice and st.button("Load Selected Sample"):
                chosen_path = sample_logos[sample_choice]
                orig_bytes = chosen_path.stat().st_size
                input_img = Image.open(chosen_path)
                input_filename = chosen_path.stem
                st.success(f"Loaded {sample_choice}")
        else:
            st.info("No sample logos currently in examples/ directory.")

    if input_img is None:
        st.info("👆 Please upload an image or select a sample logo above to begin conversion.")
        return

    # Run Conversion
    with st.spinner("Converting logo to scalable vector SVG..."):
        options = ConversionOptions(
            preset=preset_name,
            bw=bw_mode,
            colors=num_colors,
            scale=scale_val,
            keep_alpha=keep_alpha,
            denoise=denoise,
            precision=precision,
            minify=minify,
            optimize=True,
            check_quality=True,
        )

        try:
            result = convert_image(input_path=input_img, options=options)
        except Exception as e:
            st.error(f"Error during vectorization: {e}")
            return

    # Visual Display
    st.markdown("---")
    st.subheader("📊 Conversion Results")

    # Metrics row
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        if result.comparison:
            st.metric(
                label="Visual Accuracy (SSIM)",
                value=f"{result.comparison.similarity_percentage:.1f}%",
                delta=f"Score: {result.comparison.ssim:.4f}",
            )
        else:
            st.metric(label="Visual Accuracy", value="N/A")

    with col_m2:
        if result.comparison:
            psnr_str = f"{result.comparison.psnr:.1f} dB" if result.comparison.psnr != float("inf") else "∞"
            st.metric(label="PSNR Fidelity", value=psnr_str)
        else:
            st.metric(label="PSNR", value="N/A")

    with col_m3:
        st.metric(
            label="Raster Original Size",
            value=format_bytes(orig_bytes or result.original_size_bytes or len(input_img.tobytes())),
            delta=f"{result.preprocess.original_size[0]}×{result.preprocess.original_size[1]} px",
            delta_color="off",
        )

    with col_m4:
        st.metric(
            label="SVG Output Size",
            value=format_bytes(result.svg_size_bytes),
            delta="Scalable Vector",
            delta_color="normal",
        )

    # Side-by-side view
    col_orig, col_svg = st.columns(2)

    with col_orig:
        st.markdown("### 🖼️ Original Raster Logo")
        st.image(input_img, use_container_width=True)

    with col_svg:
        st.markdown("### ✨ Scalable Vector SVG")
        # Render SVG directly in HTML for crisp vector scaling
        st.markdown(
            f'<div style="background-color: #ffffff; padding: 16px; border-radius: 8px; border: 1px solid #ddd; text-align: center;">'
            f'{result.svg_content}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Download Button & Code view
    col_d1, col_d2 = st.columns([1, 3])
    with col_d1:
        st.download_button(
            label="⬇️ Download SVG File",
            data=result.svg_content,
            file_name=f"{input_filename}.svg",
            mime="image/svg+xml",
            use_container_width=True,
        )

    with st.expander("🔍 View Generated SVG Code"):
        st.code(result.svg_content, language="xml")


if __name__ == "__main__":
    main()
