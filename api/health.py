from http.server import BaseHTTPRequestHandler
import json
import sys

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        payload = {
            "status": "healthy",
            "runtime": "Vercel Serverless Python",
            "python": sys.version,
            "platform": sys.platform,
        }
        self.wfile.write(json.dumps(payload, indent=2).encode('utf-8'))
