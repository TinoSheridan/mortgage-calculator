#!/usr/bin/env python3
"""Simple startup script for the mortgage calculator."""

import os
import sys

# Set SECRET_KEY for development
os.environ['SECRET_KEY'] = 'dev-test-key-for-local-testing-only'

# Add the current directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Run the app
if __name__ == "__main__":
    from app import app
    print("=" * 50)
    print("🏠 Mortgage Calculator Starting")
    print("=" * 50)
    print("📍 URL: http://127.0.0.1:5000")
    print("🔧 Admin: http://127.0.0.1:5000/admin")
    print("💬 Chat: Available on main page")
    print("📊 Health: http://127.0.0.1:5000/health")
    print("=" * 50)
    
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=False  # Disable reloader to prevent issues
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
