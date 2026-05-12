"""WSGI entry point."""
from app import app

if __name__ == "__main__":
    app.run(port=8013, debug=True)
