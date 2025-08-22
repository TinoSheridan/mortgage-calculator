"""Ultra-simple test app for Render deployment."""

import os

from flask import Flask, jsonify

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test-key")


@app.route("/")
def home():
    """Home endpoint."""
    return jsonify({"status": "working", "message": "Ultra-simple app is running"})


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "version": "test"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
