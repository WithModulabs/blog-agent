---
name: FastAPI Testing
description: FastAPI 애플리케이션의 테스트를 효과적으로 작성하는 방법
---

# FastAPI 테스트 작성

## 개요
이 스킬은 FastAPI 애플리케이션에 대한 단위 테스트, 통합 테스트, E2E 테스트를 작성하는 방법을 안내합니다.

## 필수 의존성

```bash
# 설치
uv add --dev pytest pytest-asyncio httpx pytest-cov

# 또는 pip
pip install pytest pytest-asyncio httpx pytest-cov
```

## pytest 설정

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
addopts = "-v --tb=short"
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

## 테스트 픽스처 설정

```python
# tests/conftest.py
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.config import settings

# 테스트용 인메모리 데이터베이스
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator:
    """테스트용 데이터베이스 세션"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db) -> Generator:
    """동기 테스트 클라이언트"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db) -> AsyncClient:
    """비동기 테스트 클라이언트"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_item_data() -> dict:
    """테스트용 샘플 아이템 데이터"""
    return {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 99.99,
        "is_active": True,
    }


@pytest.fixture
def auth_headers() -> dict:
    """인증 헤더 (테스트용 토큰)"""
    # 실제 구현에서는 테스트용 토큰 생성 로직 필요
    return {"Authorization": "Bearer test-token"}
```

## 동기 테스트 예제

```python
# tests/api/test_items.py
import pytest
from fastapi import status


class TestItemsAPI:
    """Items API 테스트"""
    
    def test_create_item(self, client, sample_item_data):
        """아이템 생성 테스트"""
        response = client.post("/api/v1/items/", json=sample_item_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_item_data["name"]
        assert data["price"] == sample_item_data["price"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_item_invalid_data(self, client):
        """유효하지 않은 데이터로 아이템 생성 시 422 에러"""
        invalid_data = {"name": "", "price": -10}
        response = client.post("/api/v1/items/", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_items(self, client, sample_item_data):
        """아이템 목록 조회 테스트"""
        # 먼저 아이템 생성
        client.post("/api/v1/items/", json=sample_item_data)
        
        response = client.get("/api/v1/items/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_items_with_pagination(self, client, sample_item_data):
        """페이지네이션 테스트"""
        # 여러 아이템 생성
        for i in range(5):
            item = sample_item_data.copy()
            item["name"] = f"Item {i}"
            client.post("/api/v1/items/", json=item)
        
        response = client.get("/api/v1/items/?skip=2&limit=2")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
    
    def test_get_item_by_id(self, client, sample_item_data):
        """아이템 상세 조회 테스트"""
        # 아이템 생성
        create_response = client.post("/api/v1/items/", json=sample_item_data)
        item_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/items/{item_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == sample_item_data["name"]
    
    def test_get_item_not_found(self, client):
        """존재하지 않는 아이템 조회 시 404 에러"""
        response = client.get("/api/v1/items/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_item(self, client, sample_item_data):
        """아이템 수정 테스트"""
        # 아이템 생성
        create_response = client.post("/api/v1/items/", json=sample_item_data)
        item_id = create_response.json()["id"]
        
        update_data = {"name": "Updated Item", "price": 199.99}
        response = client.put(f"/api/v1/items/{item_id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Item"
        assert data["price"] == 199.99
    
    def test_delete_item(self, client, sample_item_data):
        """아이템 삭제 테스트"""
        # 아이템 생성
        create_response = client.post("/api/v1/items/", json=sample_item_data)
        item_id = create_response.json()["id"]
        
        response = client.delete(f"/api/v1/items/{item_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 삭제 확인
        get_response = client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
```

## 비동기 테스트 예제

```python
# tests/api/test_items_async.py
import pytest
from fastapi import status


@pytest.mark.asyncio
class TestItemsAsyncAPI:
    """Items API 비동기 테스트"""
    
    async def test_create_and_get_item(self, async_client, sample_item_data):
        """아이템 생성 및 조회 비동기 테스트"""
        # 생성
        create_response = await async_client.post(
            "/api/v1/items/",
            json=sample_item_data,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        item_id = create_response.json()["id"]
        
        # 조회
        get_response = await async_client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["name"] == sample_item_data["name"]
    
    async def test_concurrent_requests(self, async_client, sample_item_data):
        """동시 요청 테스트"""
        import asyncio
        
        async def create_item(suffix: int):
            data = sample_item_data.copy()
            data["name"] = f"Item {suffix}"
            return await async_client.post("/api/v1/items/", json=data)
        
        # 동시에 5개 아이템 생성
        tasks = [create_item(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        assert all(r.status_code == status.HTTP_201_CREATED for r in responses)
```

## 서비스 레이어 테스트

```python
# tests/services/test_item_service.py
import pytest
from app.services.item_service import ItemService
from app.schemas.item import ItemCreate, ItemUpdate


class TestItemService:
    """ItemService 단위 테스트"""
    
    def test_create_item(self, db, sample_item_data):
        """아이템 생성 서비스 테스트"""
        service = ItemService(db)
        item_in = ItemCreate(**sample_item_data)
        
        item = service.create(item_in)
        
        assert item.id is not None
        assert item.name == sample_item_data["name"]
    
    def test_get_item(self, db, sample_item_data):
        """아이템 조회 서비스 테스트"""
        service = ItemService(db)
        item_in = ItemCreate(**sample_item_data)
        created = service.create(item_in)
        
        item = service.get(created.id)
        
        assert item is not None
        assert item.id == created.id
    
    def test_update_item(self, db, sample_item_data):
        """아이템 수정 서비스 테스트"""
        service = ItemService(db)
        item_in = ItemCreate(**sample_item_data)
        created = service.create(item_in)
        
        update_data = ItemUpdate(name="Updated Name")
        updated = service.update(created.id, update_data)
        
        assert updated.name == "Updated Name"
        assert updated.price == sample_item_data["price"]  # 변경되지 않은 필드
    
    def test_delete_item(self, db, sample_item_data):
        """아이템 삭제 서비스 테스트"""
        service = ItemService(db)
        item_in = ItemCreate(**sample_item_data)
        created = service.create(item_in)
        
        result = service.delete(created.id)
        
        assert result is True
        assert service.get(created.id) is None
```

## 테스트 실행 명령어

```bash
# 모든 테스트 실행
pytest

# 특정 파일 테스트
pytest tests/api/test_items.py

# 특정 테스트 함수 실행
pytest tests/api/test_items.py::TestItemsAPI::test_create_item

# 커버리지 리포트
pytest --cov=app --cov-report=html

# 병렬 실행 (pytest-xdist 필요)
pytest -n auto

# 실패한 테스트만 재실행
pytest --lf

# 상세 출력
pytest -v --tb=long
```

## 테스트 모킹

```python
# tests/test_external.py
from unittest.mock import AsyncMock, patch
import pytest


@pytest.mark.asyncio
async def test_external_api_call(async_client):
    """외부 API 호출 모킹"""
    mock_response = {"data": "mocked data"}
    
    with patch("app.services.external_service.fetch_data") as mock_fetch:
        mock_fetch.return_value = mock_response
        
        response = await async_client.get("/api/v1/external/")
        
        assert response.status_code == 200
        mock_fetch.assert_called_once()
```

## 체크리스트

- [ ] 테스트 의존성 설치 (`pytest`, `pytest-asyncio`, `httpx`)
- [ ] `conftest.py` 픽스처 설정
- [ ] 테스트용 데이터베이스 설정
- [ ] API 엔드포인트 테스트 작성
- [ ] 서비스 레이어 테스트 작성
- [ ] 에러 케이스 테스트 포함
- [ ] 커버리지 80% 이상 달성
- [ ] CI/CD 파이프라인에 테스트 통합
