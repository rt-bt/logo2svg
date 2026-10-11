from flask import Flask, jsonify

app = Flask(__name__)
handler = app

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

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@app.route("/", methods=["GET", "OPTIONS"], strict_slashes=False)
@app.route("/api/samples", methods=["GET", "OPTIONS"], strict_slashes=False)
def get_samples():
    return jsonify({"samples": SAMPLES})
