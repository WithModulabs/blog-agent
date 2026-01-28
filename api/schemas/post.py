from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class PostBase(BaseModel):
    """블로그 포스트 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=200, description="포스트 제목")
    content: str = Field(..., min_length=1, description="포스트 본문")
    tags: List[str] = Field(default_factory=list, description="태그 목록")


class PostCreate(PostBase):
    """포스트 생성 스키마"""
    pass


class PostUpdate(BaseModel):
    """포스트 수정 스키마 - 모든 필드 선택적"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None


class PostResponse(PostBase):
    """포스트 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
