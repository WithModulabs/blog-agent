import sys
from pathlib import Path

# Add backand directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.post_service import PostService


@pytest.fixture(scope="function")
def client():
    """FastAPI 테스트 클라이언트"""
    PostService.reset()
    with TestClient(app) as c:
        yield c
    PostService.reset()


@pytest.fixture
def sample_post_data() -> dict:
    """테스트용 샘플 포스트 데이터"""
    return {
        "title": "테스트 포스트",
        "content": "이것은 테스트 포스트 내용입니다.",
        "tags": ["테스트", "FastAPI"],
    }
