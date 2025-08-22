#!/usr/bin/env python3
"""Absolute minimal test app for Render."""

import http.server
import json
import os
import socketserver


class SimpleHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP handler."""

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = json.dumps({"status": "healthy", "version": "minimal"})
            self.wfile.write(response.encode())
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = json.dumps({"message": "Minimal test app is working"})
            self.wfile.write(response.encode())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    with socketserver.TCPServer(("", port), SimpleHandler) as httpd:
        print(f"Serving on port {port}")
        httpd.serve_forever()
