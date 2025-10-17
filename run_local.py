#!/usr/bin/env python3
"""
Local development runner for Intelligent Document Agent
"""

import os
import sys
import subprocess

def main():
    """Run the Flask application locally"""
    print("[STARTING] Starting Intelligent Document Agent (Local Development)")
    print("=" * 60)

    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("[WARNING] Warning: Virtual environment not detected!")
        print("   Please activate the virtual environment first:")
        print("   .venv\\Scripts\\activate (Windows)")
        print("   source .venv/bin/activate (Linux/Mac)")
        print()

    # Check if required packages are installed
    try:
        import flask
        import torch
        import transformers
        print("[OK] Dependencies check passed")
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return 1

    # Start the Flask application
    print("[WEB] Starting web server...")
    print("   Web Interface: http://localhost:5000")
    print("   API Endpoint: http://localhost:5000/api/summarize")
    print("   Press Ctrl+C to stop")
    print()

    try:
        # Run the app
        os.system(".venv\\Scripts\\python.exe app.py")
    except KeyboardInterrupt:
        print("\n[STOP] Server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == "__main__":
    exit(main())