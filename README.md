# Blog Agent: 네이버 블로그 생성기

## 소개
Blog Agent는 **LangGraph** 기반의 멀티에이전트 파이프라인으로, 네이버 블로그 포스트를 자동 생성하는 백엔드 시스템입니다. LangChain, OpenAI API 등 최신 AI/LLM 기술을 활용하여 주제 리서치부터 SEO 최적화, 콘텐츠 작성, 이미지 생성까지 전 과정을 자동화합니다.

- **주요 기능**
  - 🔍 **웹 검색 및 콘텐츠 스크래핑**: Tavily API를 활용한 실시간 자료 수집
  - 📈 **SEO 분석 및 최적화**: 네이버 SEO 트렌드 기반 태그 및 키워드 추천 (최대 30개)
  - ✍️ **블로그 초안 자동 작성**: 마크다운 형식의 고품질 콘텐츠 생성
  - 🎨 **DALL-E 이미지 생성**: 블로그 주제에 맞는 대표 이미지 자동 생성
  - 🤖 **모듈형 에이전트 구조**: 확장과 커스터마이징이 용이한 설계
  - 🔄 **LLM 자동 폴백**: OpenAI, Gemini, Claude 중 사용 가능한 모델 자동 선택

## 폴더 구조

```
blog-agent/
├── README.md                    # 프로젝트 소개 문서
├── CONTRIBUTING.md              # 기여 가이드라인
├── LICENSE                      # 라이선스 파일
├── blog-agent.code-workspace    # VS Code 워크스페이스 설정
├── vercel.json                  # Vercel 배포 설정
│
└── backand/                     # 백엔드 서버
    ├── pyproject.toml           # 의존성 명세
    ├── langgraph.json           # LangGraph 설정
    ├── uv.lock                  # 패키지 잠금 파일
    ├── .env.example             # 환경변수 템플릿
    │
    ├── api/                     # FastAPI 기반 REST API (Vercel 배포용)
    │   ├── index.py             # Vercel 진입점
    │   ├── main.py              # FastAPI 앱 설정
    │   ├── config.py            # API 설정
    │   ├── dependencies.py      # 의존성 주입
    │   ├── routes/              # 라우트 핸들러
    │   │   ├── blog.py          # 블로그 생성 API
    │   │   ├── chat.py          # 채팅 API
    │   │   └── health.py        # 헬스체크 API
    │   └── schemas/             # Pydantic 스키마
    │       ├── blog.py
    │       ├── chat.py
    │       └── health.py
    │
    ├── app/                     # FastAPI 앱 (로컬 개발용)
    │   ├── main.py              # FastAPI 앱 진입점
    │   ├── config.py            # 앱 설정
    │   ├── api/v1/              # API v1 라우터
    │   │   ├── router.py
    │   │   └── endpoints/
    │   │       └── posts.py     # 포스트 엔드포인트
    │   ├── schemas/             # 스키마 정의
    │   │   └── post.py
    │   └── services/            # 비즈니스 로직
    │       └── post_service.py
    │
    ├── casts/                   # 멀티에이전트 파이프라인 코어
    │   ├── base_graph.py        # 그래프 기본 클래스
    │   ├── base_node.py         # 노드 기본 클래스
    │   │
    │   ├── chat/                # 채팅 에이전트 모듈
    │   │   ├── graph.py         # LangGraph 워크플로우 정의
    │   │   └── modules/         # 모듈 컴포넌트
    │   │       ├── agents.py    # 에이전트 정의
    │   │       ├── nodes.py     # 노드 구현
    │   │       ├── state.py     # 상태 관리
    │   │       ├── prompts.py   # 프롬프트 템플릿
    │   │       ├── tools.py     # 도구 정의
    │   │       ├── models.py    # 데이터 모델
    │   │       ├── conditions.py    # 조건 분기 로직
    │   │       ├── middlewares.py   # 미들웨어
    │   │       └── utils.py     # 유틸리티 함수
    │   │
    │   └── blog_writer/         # 블로그 작성 에이전트 모듈
    │       ├── graph.py         # 블로그 작성 워크플로우
    │       └── modules/         # 모듈 컴포넌트
    │           ├── agents.py    # 에이전트 정의
    │           ├── nodes.py     # 노드 구현
    │           ├── state.py     # 상태 관리
    │           ├── prompts.py   # 프롬프트 템플릿
    │           ├── tools.py     # 도구 정의 (웹 검색, 이미지 생성 등)
    │           ├── models.py    # 데이터 모델
    │           ├── conditions.py    # 조건 분기 로직
    │           ├── middlewares.py   # 미들웨어
    │           └── utils.py     # 유틸리티 함수
    │
    └── tests/                   # 테스트 코드
        ├── api_tests/           # API 테스트
        │   ├── conftest.py
        │   └── test_health.py
        ├── cast_tests/          # 에이전트 파이프라인 테스트
        │   ├── conftest.py
        │   ├── chat_test.py
        │   ├── blog_writer_test.py
        │   └── test_blog_writer_nodes.py
        └── node_tests/          # 노드 단위 테스트
            └── test_node.py
```

### 주요 디렉토리 설명
- **backand/api/**: Vercel 배포용 FastAPI REST API 서버
- **backand/app/**: 로컬 개발용 FastAPI 앱
- **backand/casts/**: 멀티에이전트 파이프라인의 핵심 구현체
  - **chat/**: 대화형 에이전트 모듈
  - **blog_writer/**: 블로그 자동 작성 에이전트 모듈
- **backand/tests/**: API, 에이전트, 노드별 테스트 코드


## 사용법
1. `.env` 파일에 아래와 같이 API 키를 입력합니다.
   ```env
   # LLM Provider (하나 이상 설정, 우선순위: OpenAI > Gemini > Claude)
   OPENAI_API_KEY=sk-...          # OpenAI API 키 (선택)
   GEMINI_API_KEY=AIza...         # Google Gemini API 키 (선택)
   ANTHROPIC_API_KEY=sk-ant-...   # Claude API 키 (선택)
   
   # 기타 서비스
   TAVILY_API_KEY=tvly-...        # 웹 검색용 (필수)
   LANGCHAIN_API_KEY=...          # LangSmith 트레이싱 (선택)
   ```

   > **💡 LLM 자동 폴백**: OpenAI 키가 없으면 자동으로 Gemini나 Claude로 전환됩니다. 최소 하나의 LLM 키만 있으면 작동합니다.

2. 개발 서버 실행:
   ```bash
   cd backand
   uv run langgraph dev
   ```



## 기여 방법

1. 이 저장소를 포크(Fork)하세요.
2. 새로운 브랜치에서 기능 추가 또는 버그 수정을 진행하세요.
3. 변경 사항을 커밋한 후, 원격 저장소에 푸시하세요.
4. Pull Request(PR)를 생성해 주세요.
5. PR에는 변경 목적, 주요 변경점, 테스트 방법 등을 명확히 작성해 주세요.

기여 전 최신 `v2-main` 브랜치와 동기화(sync)하는 것을 권장합니다.

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

