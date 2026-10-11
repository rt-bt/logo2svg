# logo2svg 🎨

[![CI](https://github.com/your-org/logo2svg/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/logo2svg/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Clean & Typed](https://img.shields.io/badge/code%20style-typed-brightgreen.svg)](https://peps.python.org/pep-0484/)

> **Production-grade raster logo to SVG vector converter.** Converts PNG, JPG, JPEG, WEBP, and BMP brand marks into clean, scalable, mathematically accurate SVG vector graphics editable in Inkscape, Illustrator, and Figma.

---

## 🌟 Key Features

### 🎨 1. Creative Studio Web Interface (HTML5 / CSS3 / JavaScript)
- **↔️ Interactive Before / After Split Slider**: Draggable curtain divider comparing original raster pixels with generated vector curves in real-time.
- **🔍 Infinite Vector Zoom & Pan Canvas**: Magnify logos up to 16x (1600%) with mouse wheel and drag-to-pan to verify razor-sharp sub-pixel edge fidelity.
- **⚡ Live Auto-Retrace**: Changing presets, B&W mode, alpha transparency, or color quantization instantly re-traces without requiring a page refresh.
- **🎨 Brand Color Palette Extractor**: Automatically detects dominant brand colors and generates interactive swatch chips with one-click hex code copying.
- **📤 Zero-Refresh Multi-Source Upload**:
  - `+ Upload Logo` button always visible in the top header.
  - Drag-and-drop images anywhere onto the window with a glowing visual overlay.
  - Direct clipboard paste support (`Ctrl + V`).
  - `📁 Upload New Logo` and `✕ Reset` buttons in the sidebar.
- **💾 One-Click Production Exports**:
  - Download `.svg` file.
  - Copy clean, minified SVG XML.
  - Copy as ready-to-use **React JSX Component** (`<Logo />`).
  - Copy as **CSS Data URI** (`data:image/svg+xml;utf8,...`).
  - Integrated syntax-highlighted **SVG Code Inspector Modal**.
- **🏁 5 Studio Canvas Backgrounds**: Dark Checkerboard, Light Checkerboard, Pitch Black (`#000`), Pure White (`#FFF`), and Blueprint Tech Grid.
- **📊 Studio Intelligence Dashboard**: Real-time SSIM structural fidelity ring (S+ Studio Grade), PSNR in dB, vector path counts, and size compression ratio.

### 💻 2. Command-Line Interface (CLI)
- **⚡ Single & Batch Processing**: Vectorize a single file or an entire directory of mixed logos in one command.
- **🎛️ Tuned Tracing Presets**:
  - `logo`: Balanced Bézier spline curves for general brand marks.
  - `sharp`: Polygon fitting with low error thresholds for geometric, angular, and tech marks.
  - `smooth`: High curvature smoothing for circular badges, crests, and emblems.
- **🧹 Preprocessing Pipeline**:
  - Automatic 2x upscaling for low-res logos (<1000px) using high-fidelity **LANCZOS** interpolation.
  - Transparency preservation (`--keep-alpha`) or clean flattening onto white.
  - Median-filter artifact denoising for lossy JPEG ringing (`--denoise`).
  - Color palette quantization to eliminate JPEG gradients (`--colors 1-8`).
- **📏 Path Optimization**:
  - Emits clean, semantic `<path>` vector geometry. Zero embedded base64 or `<image>` rasters.
  - Embeds mathematically accurate `viewBox` coordinates for infinite scalability.
  - Minifies redundant transforms and rounds coordinates to custom decimal precision (`--precision 1-4`).
- **📈 Quality Verification**: Automatically calculates SSIM (Structural Similarity Index) and PSNR against the input raster.

---

## 📊 Benchmark Fidelity on Sample Logos

| Logo Type | Sample File | Preset | Original | SVG Size | SSIM Score | Visual Match | PSNR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tech Shield** | `tech_shield.png` | `logo` | 3.8 KB | 64.9 KB | **0.9993** | **99.93%** | 45.7 dB |
| **Geometric Hexagon** | `geometric_logo.png` | `sharp` | 3.2 KB | 16.6 KB | **0.9986** | **99.86%** | 42.9 dB |
| **Curved Badge Emblem**| `smooth_badge.png` | `smooth`| 5.2 KB | 104.4 KB | **0.9966** | **99.66%** | 37.3 dB |
| **Retro Crest (Lossy JPG)**| `retro_crest.jpg` | `logo` (`--denoise`)| 10.0 KB | 333.8 KB | **0.9693** | **96.93%** | 32.2 dB |
| **Transparent Symbol** | `transparent_icon.png` | `logo` (`--keep-alpha`)| 2.3 KB | 126.8 KB | **0.9575** | **95.75%** | 26.2 dB |

---

## 📥 Installation Guide

### Prerequisites
- Python **3.10** or higher (`3.10`, `3.11`, `3.12`, `3.13`, `3.14`)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/logo2svg.git
cd logo2svg
```

### 2. Setup Virtual Environment

#### 🪟 Windows (PowerShell / Command Prompt)
```powershell
# Create virtual environment
py -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies and package in editable mode
pip install -e ".[ui,dev]"
```
> *Windows Note*: SVG rendering for quality verification automatically uses `resvg-py` out-of-the-box, requiring **zero** external C libraries or GTK/Cairo DLLs.

#### 🍎 macOS
```bash
# Optional: install Cairo library
brew install cairo

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install logo2svg
pip install -e ".[ui,dev]"
```

#### 🐧 Linux (Ubuntu / Debian / Fedora)
```bash
# Install Cairo build dependencies
sudo apt-get update && sudo apt-get install -y libcairo2-dev pkg-config

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install logo2svg
pip install -e ".[ui,dev]"
```

---

## 🚀 How to Use

### Method 1: Creative Studio Web Interface (Recommended)

Launch the modern standalone Creative Studio web app:

```bash
# Start Web Studio
python server.py
# or via CLI flag
logo2svg --web
# on Windows (if py launcher is default)
py server.py
```

The browser opens automatically at **`http://127.0.0.1:5000`**.

#### What you can do in Creative Studio:
1. **Upload**: Drag and drop any logo or paste directly from clipboard (`Ctrl + V`).
2. **Inspect**: Drag the center split divider to compare raster vs SVG vector curves.
3. **Zoom**: Scroll your mouse wheel inside the canvas to inspect sub-pixel splines up to 16x.
4. **Tune**: Select `Logo`, `Sharp`, or `Smooth` presets — changes update live in real-time.
5. **Palette**: Click any extracted brand color chip to copy the hex code.
6. **Export**: Click `Download SVG`, `Copy SVG`, `Copy React JSX`, or `Copy Data URI`.

---

### Method 2: Command-Line Interface (CLI)

```bash
# Convert a single logo (outputs logo.svg in the same directory)
logo2svg logo.png

# Specify custom output path
logo2svg logo.png -o output/vector_logo.svg

# Batch convert an entire folder of logos
logo2svg my_logos/ -o converted_svgs/
```

#### Preset Examples
```bash
# 1. Balanced Brand Mark (smooth Bézier splines)
logo2svg company_logo.png --preset logo

# 2. Geometric / Tech / Angular Mark (polygon edge fitting)
logo2svg tech_shield.png --preset sharp

# 3. Badge / Vintage / Circular Emblem (enhanced smoothing)
logo2svg crest.png --preset smooth
```

#### Advanced CLI Tuning Flags
```bash
# Pure monochrome silhouette (black & white vector paths)
logo2svg symbol.png --bw

# Clean JPEG compression artifacts with median filter
logo2svg scanned.jpg --denoise --preset logo

# Quantize noisy gradients into 4 solid Pantone-style colors
logo2svg badge.png --colors 4

# Preserve transparent PNG background
logo2svg icon.png --keep-alpha

# Minify XML output into single-line format
logo2svg brand.png --minify --precision 2
```

#### CLI Flags Reference

| Flag | Argument | Description | Default |
| :--- | :--- | :--- | :--- |
| `input` | `FILE \| DIR` | Input raster image or directory of images | *Required* |
| `-o`, `--output` | `PATH` | Output SVG file path or directory | Same as input (`.svg`) |
| `--preset` | `logo \| sharp \| smooth` | Tracing parameter preset | `logo` |
| `--bw` | *flag* | Binarizes logo to pure black & white vectors | `False` |
| `--colors` | `1-8` | Quantize image palette to N colors | `None` (full) |
| `--scale` | `FLOAT` | Custom upscale factor (auto 2x if <1000px) | Auto |
| `--keep-alpha` | *flag* | Preserve transparency instead of flattening | `False` |
| `--denoise` | *flag* | Apply median filter denoising for JPG artifacts | `False` |
| `--precision` | `INT` | Decimal coordinate precision for paths | `2` |
| `--minify` | *flag* | Compact single-line SVG output | `False` |
| `--web` | *flag* | Launch Creative Studio Web Application | `False` |
| `--no-optimize`| *flag* | Skip SVG coordinate optimization | `False` |
| `--no-check` | *flag* | Skip SSIM quality comparison calculation | `False` |

---

### Method 3: Python API

You can import and use `logo2svg` directly inside your own Python applications:

```python
from logo2svg import convert_image, ConversionOptions

# Configure conversion options
options = ConversionOptions(
    preset="logo",        # "logo", "sharp", or "smooth"
    bw=False,             # Monochrome mode
    keep_alpha=True,      # Preserve transparency
    denoise=True,         # JPEG noise filter
    precision=2,          # Decimal precision
    minify=True,          # Minified XML output
)

# Convert raster image to SVG
result = convert_image("logo.png", output_path="logo.svg", options=options)

print(f"SVG generated: {len(result.svg_content)} bytes")
print(f"Visual match (SSIM): {result.similarity_percentage:.2f}%")
print(f"Signal fidelity (PSNR): {result.comparison.psnr:.1f} dB")
```

---

### Method 4: Streamlit Studio Edition

For rapid prototyping in Streamlit:

```bash
streamlit run app.py
```
*Opens at `http://localhost:8501`*.

---

## 🏗️ Project Architecture

```
logo2svg/
├── src/
│   └── logo2svg/
│       ├── __init__.py       # Package exports & version
│       ├── cli.py            # CLI entrypoint & argument parsing
│       ├── converter.py      # Core conversion orchestrator
│       ├── preprocess.py     # Image validation, alpha flattening, LANCZOS scaling, denoising
│       ├── trace.py          # vtracer engine integration & preset configurations
│       ├── optimize.py       # SVG cleanup, viewBox injection, transform stripping, precision rounding
│       └── compare.py        # SSIM and PSNR fidelity verification pipeline
├── web/                      # Standalone Creative Studio Web Application
│   ├── index.html            # Studio application shell & modals
│   ├── style.css             # High-contrast Creative Studio dark theme & animations
│   └── app.js                # Interactive split slider, infinite zoom & pan, exports
├── examples/                 # Benchmark test logos (PNG, JPG, SVG)
├── tests/                    # Comprehensive unit and integration test suite
│   ├── test_preprocess.py
│   ├── test_trace.py
│   ├── test_optimize.py
│   ├── test_compare.py
│   ├── test_cli.py
│   └── test_server.py
├── server.py                 # High-performance Flask server & REST API
├── app.py                    # Streamlit Studio web app
├── pyproject.toml            # Modern PEP 517/621 build configuration
├── requirements.txt          # Python package requirements
└── README.md                 # Complete documentation
```

---

## 🧪 Running Tests

The test suite contains 47 unit and integration tests covering the entire pipeline:

```bash
# Run all tests
pytest -v

# Run with test coverage
pytest --cov=logo2svg tests/
```

All 47 tests pass in ~1 second.

---

## 💡 Pro Tips & Best Practices

1. **Which preset to choose?**
   - **`sharp`**: Hexagonal, angular, tech shields, and logos with crisp straight lines.
   - **`smooth`**: Badges, emblems, circular marks, mascots, and cursive fonts.
   - **`logo`**: Standard corporate brand marks with mixed geometry and curves.
2. **JPEG compression noise**:
   - If your input logo is a compressed JPEG with visible pixel noise or ringing, always pass `--denoise` or enable "Smart Denoise" in the Web Studio.
3. **Multi-color logos**:
   - Use `--colors 4` to snap gradient noise into solid Pantone-style color blocks.
4. **Transparency**:
   - For logos with cutouts or transparent backgrounds, enable `--keep-alpha`.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
