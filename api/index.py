"""Vercel serverless handler for FastAPI app."""

import sys
import os
from pathlib import Path

# Add project root to sys.path
# This ensures that 'import api.main' works correctly on Vercel
path = Path(__file__).resolve().parent.parent
if str(path) not in sys.path:
    sys.path.insert(0, str(path))

# Set environment variable for Vercel
os.environ["VERCEL"] = "1"

try:
    # Try to import the fully configured app from api/main.py
    from api.main import app
except Exception as e:
    # If import fails, create a minimal app that reports the error.
    # This helps diagnose missing dependencies or path issues on Vercel.
    from fastapi import FastAPI
    app = FastAPI(title="Blog Agent API (Import Error)")
    
    @app.get("/")
    async def debug_root():
        import traceback
        return {
            "error": "Import failed",
            "message": str(e),
            "traceback": traceback.format_exc(),
            "sys_path": sys.path,
            "cwd": os.getcwd(),
            "api_dir_exists": Path("api").exists(),
            "api_main_exists": Path("api/main.py").exists()
        }
    
    @app.get("/health")
    async def health():
        return {"status": "error", "message": str(e), "mode": "error_fallback"}
