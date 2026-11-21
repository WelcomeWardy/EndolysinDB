"""
run.py — Development server entry point.

Usage:
    python run.py

Also used by Flask CLI via .flaskenv (FLASK_APP=run.py).
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
