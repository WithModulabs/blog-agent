# Blog Agent: 네이버 블로그 생성기

## 소개
Blog Agent는 LangGraph, LangChain, OpenAI, Streamlit 등 최신 AI/LLM 프레임워크를 활용하여 네이버 블로그 포스트를 자동으로 생성하는 멀티에이전트 파이프라인 프로젝트입니다. 

- **주요 기능**
  - 웹 검색 및 콘텐츠 스크래핑
  - SEO 분석 및 최적화 태그 추천
  - 블로그 초안 자동 작성 (마크다운)
  - DALL-E 기반 대표 이미지 프롬프트 생성 및 이미지 생성
  - 전체 파이프라인을 Streamlit UI로 손쉽게 실행

## 폴더 구조

```
blog-agent/
├── main.py
├── pyproject.toml
├── README.md
├── .env
├── .gitignore
├── .python-version
├── uv.lock
```
- `main.py` : 전체 멀티에이전트 파이프라인 및 Streamlit UI
- `.env` : API 키 환경변수 파일
- `pyproject.toml` : 프로젝트 의존성 명세


## 에이전트 구성
- **Researcher**: 주제 관련 웹 검색 및 자료 수집
- **SEO Specialist**: 최신 네이버 SEO 트렌드 분석 및 태그 추천
- **Writer**: SEO 분석 결과를 바탕으로 블로그 초안 작성
- **Art Director**: 블로그 제목/내용 기반 대표 이미지 프롬프트 및 이미지 생성

## 사용법
1. `.env` 파일에 아래와 같이 API 키를 입력합니다.
   ```env
   OPENAI_API_KEY=sk-...
   TAVILY_API_KEY=tvly-...
   # (필요시) LANGCHAIN_API_KEY=...
   ```
2. 가상환경 생성 및 의존성 설치 (uv 사용 권장)
   ```powershell
   uv venv
   .\.venv\Scripts\Activate.ps1
   uv sync
   ```
3. Streamlit 앱 실행
   ```bash
   uv run streamlit run main.py
   ```


## 기여 방법

1. 이 저장소를 포크(Fork)하세요.
2. 새로운 브랜치에서 기능 추가 또는 버그 수정을 진행하세요.
3. 변경 사항을 커밋한 후, 원격 저장소에 푸시하세요.
4. Pull Request(PR)를 생성해 주세요.
5. PR에는 변경 목적, 주요 변경점, 테스트 방법 등을 명확히 작성해 주세요.

기여 전 최신 `master` 브랜치와 동기화(sync)하는 것을 권장합니다.

이슈나 개선 제안도 언제든 환영합니다!   
소통방 : https://open.kakao.com/o/gbTuFgOh



## 참고
- LangGraph: https://github.com/langchain-ai/langgraph
- LangChain: https://github.com/langchain-ai/langchain
- Tavily: https://python.langchain.com/docs/integrations/tools/tavily_search
- DALL-E: https://platform.openai.com/docs/guides/images

---

본 프로젝트는 '모두의 연구소' AI 에이전트랩에 관심 있는 분들을 위한 예제/데모 목적입니다.
https://modulabs.co.kr/community/momos/284

