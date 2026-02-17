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
except Exception as import_error:
    # If import fails, create a minimal app that reports the error.
    # This helps diagnose missing dependencies or path issues on Vercel.
    import traceback

    from fastapi import FastAPI

    _error_message = str(import_error)
    _error_traceback = traceback.format_exc()
    _is_debug = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")

    app = FastAPI(title="Blog Agent API (Import Error)")

    @app.get("/")
    async def debug_root():
        # Only expose detailed error info in debug mode
        response = {"error": "Import failed", "message": _error_message}
        if _is_debug:
            response.update(
                {
                    "traceback": _error_traceback,
                    "sys_path": sys.path,
                    "cwd": os.getcwd(),
                    "api_dir_exists": Path("api").exists(),
                    "api_main_exists": Path("api/main.py").exists(),
                }
            )
        return response

    @app.get("/health")
    async def health():
        return {"status": "error", "message": _error_message, "mode": "error_fallback"}
