import sys
from flask import Flask, jsonify

app = Flask(__name__)
handler = app

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.route("/", strict_slashes=False)
@app.route("/api/health", strict_slashes=False)
def health():
    return jsonify({
        "status": "healthy",
        "runtime": "Vercel Serverless Function",
        "python": sys.version,
    })
