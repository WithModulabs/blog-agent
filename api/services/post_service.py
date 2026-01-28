from datetime import datetime
from typing import Optional, List

from api.schemas.post import PostCreate, PostUpdate, PostResponse


class PostService:
    """블로그 포스트 서비스 (인메모리 저장소)"""
    
    # 인메모리 저장소 (데모용)
    _posts: dict[int, dict] = {}
    _counter: int = 0

    @classmethod
    def reset(cls) -> None:
        """저장소 초기화 (테스트용)"""
        cls._posts = {}
        cls._counter = 0

    @classmethod
    def create(cls, post_in: PostCreate) -> PostResponse:
        """새 포스트 생성"""
        cls._counter += 1
        now = datetime.now()
        post_data = {
            "id": cls._counter,
            "title": post_in.title,
            "content": post_in.content,
            "tags": post_in.tags,
            "created_at": now,
            "updated_at": None,
        }
        cls._posts[cls._counter] = post_data
        return PostResponse(**post_data)

    @classmethod
    def get(cls, post_id: int) -> Optional[PostResponse]:
        """포스트 조회"""
        post_data = cls._posts.get(post_id)
        if post_data:
            return PostResponse(**post_data)
        return None

    @classmethod
    def get_multi(
        cls,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[PostResponse]:
        """포스트 목록 조회"""
        posts = list(cls._posts.values())
        
        if search:
            posts = [
                p for p in posts
                if search.lower() in p["title"].lower()
                or search.lower() in p["content"].lower()
            ]
        
        posts = sorted(posts, key=lambda x: x["created_at"], reverse=True)
        return [PostResponse(**p) for p in posts[skip:skip + limit]]

    @classmethod
    def update(cls, post_id: int, post_update: PostUpdate) -> Optional[PostResponse]:
        """포스트 수정"""
        if post_id not in cls._posts:
            return None
        
        post_data = cls._posts[post_id]
        update_dict = post_update.model_dump(exclude_unset=True)
        
        for key, value in update_dict.items():
            post_data[key] = value
        
        post_data["updated_at"] = datetime.now()
        cls._posts[post_id] = post_data
        
        return PostResponse(**post_data)

    @classmethod
    def delete(cls, post_id: int) -> bool:
        """포스트 삭제"""
        if post_id in cls._posts:
            del cls._posts[post_id]
            return True
        return False
