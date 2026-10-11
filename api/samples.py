from http.server import BaseHTTPRequestHandler
import json

SAMPLES = [
    {
        "id": "geometric_logo",
        "filename": "geometric_logo.png",
        "title": "Geometric Mark",
        "category": "Geometric",
        "description": "Clean shapes & angles",
        "url": "/examples/geometric_logo.png",
        "size_bytes": 3246,
    },
    {
        "id": "tech_shield",
        "filename": "tech_shield.png",
        "title": "Tech Shield",
        "category": "Icon",
        "description": "Sharp modern cybersecurity badge",
        "url": "/examples/tech_shield.png",
        "size_bytes": 3901,
    },
    {
        "id": "smooth_badge",
        "filename": "smooth_badge.png",
        "title": "Smooth Badge",
        "category": "Badge",
        "description": "Curved gradients & borders",
        "url": "/examples/smooth_badge.png",
        "size_bytes": 5321,
    },
    {
        "id": "transparent_icon",
        "filename": "transparent_icon.png",
        "title": "Alpha Icon",
        "category": "Transparent",
        "description": "Transparent PNG mark",
        "url": "/examples/transparent_icon.png",
        "size_bytes": 2372,
    },
    {
        "id": "retro_crest",
        "filename": "retro_crest.jpg",
        "title": "Retro Crest",
        "category": "Vintage",
        "description": "Detailed vintage emblem",
        "url": "/examples/retro_crest.jpg",
        "size_bytes": 10205,
    },
]

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"samples": SAMPLES}).encode('utf-8'))
