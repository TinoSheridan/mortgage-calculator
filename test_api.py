"""
Minimal test API to debug Railway deployment issues
"""

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for GitHub Pages
CORS(
    app,
    origins=[
        "https://tinosheridan.github.io",  # GitHub Pages URL
        "http://localhost:3000",  # For local development
        "http://127.0.0.1:3000",  # For local development
        "http://localhost:5000",  # Local Flask development
        "http://127.0.0.1:5000",  # Local Flask development
    ],
    supports_credentials=True,
)


@app.route("/health")
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "2.8.0-minimal",
        "timestamp": "2025-08-22T02:30:00Z"
    })


@app.route("/")
def home():
    """Root endpoint"""
    return jsonify({
        "message": "Mortgage Calculator API - Minimal Test Version",
        "version": "2.8.0-minimal",
        "endpoints": ["/health"]
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)