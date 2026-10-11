"""Vercel serverless entrypoint for logo2svg Creative Studio."""

import sys
from pathlib import Path

# Add root directory and src to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from server import app

# Export WSGI application for Vercel Python runtime
app = app
