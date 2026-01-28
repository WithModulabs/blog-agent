"""Vercel serverless handler for FastAPI app."""

import sys
from pathlib import Path

# Add backand directory to path for imports
# When deployed from project root, we need to add the backand directory
backand_path = Path(__file__).parent.parent
sys.path.insert(0, str(backand_path))

from api.main import app

# Vercel expects the app to be named 'app' or 'handler'
# FastAPI app is already named 'app', so Vercel will automatically use it
