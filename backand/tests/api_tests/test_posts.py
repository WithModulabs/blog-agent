"""Posts API 테스트"""

from fastapi import status


class TestHealthCheck:
    """헬스체크 엔드포인트 테스트"""
    
    def test_health_check(self, client):
        """헬스체크 응답 확인"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "healthy"}


class TestPostsAPI:
    """Posts API CRUD 테스트"""
    
    def test_create_post(self, client, sample_post_data):
        """포스트 생성 테스트"""
        response = client.post("/api/v1/posts/", json=sample_post_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == sample_post_data["title"]
        assert data["content"] == sample_post_data["content"]
        assert data["tags"] == sample_post_data["tags"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_post_invalid_data(self, client):
        """유효하지 않은 데이터로 포스트 생성 시 422 에러"""
        invalid_data = {"title": "", "content": ""}
        response = client.post("/api/v1/posts/", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_posts(self, client, sample_post_data):
        """포스트 목록 조회 테스트"""
        # 포스트 생성
        client.post("/api/v1/posts/", json=sample_post_data)
        
        response = client.get("/api/v1/posts/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
    
    def test_get_posts_with_search(self, client, sample_post_data):
        """검색 테스트"""
        client.post("/api/v1/posts/", json=sample_post_data)
        client.post("/api/v1/posts/", json={
            "title": "다른 포스트",
            "content": "다른 내용",
            "tags": [],
        })
        
        response = client.get("/api/v1/posts/?search=테스트")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "테스트 포스트"
    
    def test_get_post_by_id(self, client, sample_post_data):
        """포스트 상세 조회 테스트"""
        create_response = client.post("/api/v1/posts/", json=sample_post_data)
        post_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/posts/{post_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == post_id
        assert data["title"] == sample_post_data["title"]
    
    def test_get_post_not_found(self, client):
        """존재하지 않는 포스트 조회 시 404 에러"""
        response = client.get("/api/v1/posts/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_post(self, client, sample_post_data):
        """포스트 수정 테스트"""
        create_response = client.post("/api/v1/posts/", json=sample_post_data)
        post_id = create_response.json()["id"]
        
        update_data = {"title": "수정된 제목", "tags": ["수정됨"]}
        response = client.put(f"/api/v1/posts/{post_id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "수정된 제목"
        assert data["content"] == sample_post_data["content"]  # 변경되지 않음
        assert data["tags"] == ["수정됨"]
        assert data["updated_at"] is not None
    
    def test_update_post_not_found(self, client):
        """존재하지 않는 포스트 수정 시 404 에러"""
        response = client.put("/api/v1/posts/99999", json={"title": "새 제목"})
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_post(self, client, sample_post_data):
        """포스트 삭제 테스트"""
        create_response = client.post("/api/v1/posts/", json=sample_post_data)
        post_id = create_response.json()["id"]
        
        response = client.delete(f"/api/v1/posts/{post_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 삭제 확인
        get_response = client.get(f"/api/v1/posts/{post_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_post_not_found(self, client):
        """존재하지 않는 포스트 삭제 시 404 에러"""
        response = client.delete("/api/v1/posts/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
