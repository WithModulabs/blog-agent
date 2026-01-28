"""Vercel serverless handler for FastAPI app."""

import sys
from pathlib import Path

# Add project root to sys.path
path = Path(__file__).resolve().parent.parent
if str(path) not in sys.path:
    sys.path.insert(0, str(path))

# Export the app from api.main directly for Vercel
try:
    from api.main import app
except Exception as e:
    # Minimal fallback for debugging if migration fails
    from fastapi import FastAPI
    app = FastAPI(title="Blog Agent API (Fallback)")
    
    @app.get("/health")
    async def health():
        return {"status": "import_error", "detail": str(e)}
    
    @app.get("/")
    async def root():
        return {"error": str(e)}
