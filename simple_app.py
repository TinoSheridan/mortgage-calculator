"""
Absolutely minimal Flask app for Railway debugging
"""

from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello Railway!"

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)