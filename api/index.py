from fastapi import FastAPI
import os
import sys
from pathlib import Path

app = FastAPI()

@app.get("/")
async def root():
    return {
        "message": "Blog Agent API is running!",
        "cwd": os.getcwd(),
        "python_version": sys.version
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "mode": "standalone_test"}

# 여기에 실제 메인 앱 임포트 시도를 주석 처리하거나 하단에 배치하여 
# 최소한 위의 health 체크는 무조건 동작하게 합니다.
try:
    from api.main import app as main_app
    app.mount("/api/v1", main_app) # 기존 앱을 하위 경로로 마운트 시도
except Exception as e:
    @app.get("/debug")
    async def debug():
        return {"import_error": str(e)}
