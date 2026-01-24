"""Vercel serverless handler for FastAPI app."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

# Vercel expects the app to be named 'app' or 'handler'
# FastAPI app is already named 'app', so Vercel will automatically use it
