---
name: FastAPI Project Setup
description: FastAPI 프로젝트의 기본 구조를 설정하고 초기화하는 방법
---

# FastAPI 프로젝트 구조 설정

## 개요
이 스킬은 FastAPI 프로젝트의 표준 디렉토리 구조를 생성하고 필수 의존성을 설정하는 방법을 안내합니다.

## 표준 프로젝트 구조

```
project_root/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 인스턴스 및 라우터 등록
│   ├── config.py            # 환경 설정 및 설정 클래스
│   ├── dependencies.py      # 공통 의존성 주입
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py    # API v1 라우터 집합
│   │   │   └── endpoints/
│   │   │       ├── __init__.py
│   │   │       └── items.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py      # 인증/보안 관련
│   │   └── logging.py       # 로깅 설정
│   ├── models/
│   │   ├── __init__.py
│   │   └── item.py          # SQLAlchemy 모델
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── item.py          # Pydantic 스키마
│   ├── services/
│   │   ├── __init__.py
│   │   └── item_service.py  # 비즈니스 로직
│   └── db/
│       ├── __init__.py
│       ├── database.py      # 데이터베이스 연결
│       └── repositories/
│           └── item_repo.py # 데이터 접근 계층
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest 픽스처
│   └── api/
│       └── test_items.py
├── alembic/                  # 마이그레이션 (선택)
├── .env                      # 환경 변수
├── .env.example
├── pyproject.toml            # 의존성 관리
├── requirements.txt          # pip 의존성 (대안)
└── README.md
```

## 초기화 단계

### 1. 프로젝트 생성

```bash
# 디렉토리 생성
mkdir my-fastapi-project
cd my-fastapi-project

# 가상환경 생성 (uv 권장)
uv venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

### 2. 의존성 설치

**pyproject.toml 사용 시:**
```toml
[project]
name = "my-fastapi-project"
version = "0.1.0"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "sqlalchemy>=2.0.0",
    "python-multipart>=0.0.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.26.0",
    "ruff>=0.1.0",
]
```

**requirements.txt 사용 시:**
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
sqlalchemy>=2.0.0
python-multipart>=0.0.6
```

### 3. 기본 main.py 생성

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 4. 설정 파일 (config.py)

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "My FastAPI Project"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### 5. 실행

```bash
# 개발 모드
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 체크리스트

- [ ] 프로젝트 디렉토리 구조 생성
- [ ] 가상환경 설정
- [ ] 의존성 설치
- [ ] main.py 생성
- [ ] config.py 설정
- [ ] .env 파일 생성
- [ ] 개발 서버 실행 확인
- [ ] `/docs` 에서 Swagger UI 접근 확인
