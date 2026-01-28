from fastapi import APIRouter, HTTPException, status, Query, Path
from typing import List, Optional

from app.schemas.post import PostCreate, PostUpdate, PostResponse
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="새 포스트 생성",
    description="새로운 블로그 포스트를 생성합니다.",
)
async def create_post(post: PostCreate) -> PostResponse:
    """새 블로그 포스트 생성"""
    return PostService.create(post)


@router.get(
    "/",
    response_model=List[PostResponse],
    summary="포스트 목록 조회",
    description="블로그 포스트 목록을 조회합니다. 검색 및 페이지네이션을 지원합니다.",
)
async def get_posts(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="반환할 최대 항목 수"),
    search: Optional[str] = Query(None, description="제목/본문 검색어"),
) -> List[PostResponse]:
    """포스트 목록 조회"""
    return PostService.get_multi(skip=skip, limit=limit, search=search)


@router.get(
    "/{post_id}",
    response_model=PostResponse,
    summary="포스트 상세 조회",
    description="지정된 ID의 블로그 포스트를 조회합니다.",
)
async def get_post(
    post_id: int = Path(..., ge=1, description="포스트 ID"),
) -> PostResponse:
    """포스트 상세 조회"""
    post = PostService.get(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found",
        )
    return post


@router.put(
    "/{post_id}",
    response_model=PostResponse,
    summary="포스트 수정",
    description="기존 블로그 포스트를 수정합니다.",
)
async def update_post(
    post_id: int = Path(..., ge=1, description="포스트 ID"),
    post_update: PostUpdate = ...,
) -> PostResponse:
    """포스트 수정"""
    post = PostService.update(post_id, post_update)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found",
        )
    return post


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="포스트 삭제",
    description="지정된 ID의 블로그 포스트를 삭제합니다.",
)
async def delete_post(
    post_id: int = Path(..., ge=1, description="포스트 ID"),
) -> None:
    """포스트 삭제"""
    success = PostService.delete(post_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found",
        )
