"""Vercel serverless handler for FastAPI app."""

import sys
from pathlib import Path

# Add backand directory to path for imports
# When deployed from project root, we need to add the backand directory
backand_path = Path(__file__).parent.parent
sys.path.insert(0, str(backand_path))

try:
    from api.main import app
except Exception as e:
    # Fallback: create minimal app for debugging
    from fastapi import FastAPI
    app = FastAPI(title="Blog Agent API (Fallback)")
    
    @app.get("/health")
    async def health():
        return {"status": "ok", "error": str(e)}
    
    @app.get("/")
    async def root():
        return {"message": "Blog Agent API (Fallback Mode)", "import_error": str(e)}

# Vercel expects the app to be named 'app' or 'handler'
# FastAPI app is already named 'app', so Vercel will automatically use it
