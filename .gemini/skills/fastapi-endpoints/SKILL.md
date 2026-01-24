---
name: FastAPI Endpoints
description: FastAPI 엔드포인트를 효과적으로 생성하고 구성하는 방법
---

# FastAPI 엔드포인트 생성

## 개요
이 스킬은 FastAPI에서 RESTful API 엔드포인트를 생성하는 모범 사례와 패턴을 제공합니다.

## 기본 엔드포인트 패턴

### 1. 라우터 설정

```python
# app/api/v1/endpoints/items.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional
from sqlalchemy.orm import Session

from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from app.services.item_service import ItemService
from app.db.database import get_db

router = APIRouter(prefix="/items", tags=["items"])
```

### 2. CRUD 엔드포인트

```python
# CREATE
@router.post(
    "/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="새 아이템 생성",
    description="새로운 아이템을 데이터베이스에 생성합니다.",
)
async def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
) -> ItemResponse:
    service = ItemService(db)
    return service.create(item)


# READ - 목록
@router.get(
    "/",
    response_model=List[ItemResponse],
    summary="아이템 목록 조회",
)
async def get_items(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="반환할 최대 항목 수"),
    search: Optional[str] = Query(None, description="검색어"),
    db: Session = Depends(get_db),
) -> List[ItemResponse]:
    service = ItemService(db)
    return service.get_multi(skip=skip, limit=limit, search=search)


# READ - 단일
@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    summary="아이템 상세 조회",
)
async def get_item(
    item_id: int = Path(..., ge=1, description="아이템 ID"),
    db: Session = Depends(get_db),
) -> ItemResponse:
    service = ItemService(db)
    item = service.get(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
        )
    return item


# UPDATE
@router.put(
    "/{item_id}",
    response_model=ItemResponse,
    summary="아이템 수정",
)
async def update_item(
    item_id: int = Path(..., ge=1),
    item_update: ItemUpdate = ...,
    db: Session = Depends(get_db),
) -> ItemResponse:
    service = ItemService(db)
    item = service.update(item_id, item_update)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
        )
    return item


# DELETE
@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="아이템 삭제",
)
async def delete_item(
    item_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
) -> None:
    service = ItemService(db)
    success = service.delete(item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
        )
```

## Pydantic 스키마

```python
# app/schemas/item.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="아이템 이름")
    description: Optional[str] = Field(None, max_length=500, description="설명")
    price: float = Field(..., gt=0, description="가격")
    is_active: bool = Field(True, description="활성화 여부")


class ItemCreate(ItemBase):
    """아이템 생성 스키마"""
    pass


class ItemUpdate(BaseModel):
    """아이템 수정 스키마 - 모든 필드 선택적"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class ItemResponse(ItemBase):
    """아이템 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
```

## 의존성 주입

```python
# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user
```

## 라우터 등록

```python
# app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1.endpoints import items, users, auth

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(items.router)
```

## 고급 패턴

### 파일 업로드

```python
from fastapi import UploadFile, File

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(..., description="업로드할 파일"),
):
    contents = await file.read()
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents),
    }
```

### 백그라운드 태스크

```python
from fastapi import BackgroundTasks

def send_notification(email: str, message: str):
    # 이메일 전송 로직
    pass

@router.post("/notify")
async def create_notification(
    email: str,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(send_notification, email, "알림 메시지")
    return {"message": "Notification queued"}
```

### WebSocket

```python
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
```

## 체크리스트

- [ ] 라우터 파일 생성 (`prefix`, `tags` 설정)
- [ ] Pydantic 스키마 정의 (Create, Update, Response)
- [ ] CRUD 엔드포인트 구현
- [ ] 적절한 HTTP 상태 코드 사용
- [ ] Path/Query 파라미터 검증
- [ ] 의존성 주입 설정
- [ ] API 문서화 (summary, description)
- [ ] 에러 핸들링
