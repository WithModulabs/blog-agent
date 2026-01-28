
# Chat 모듈 (Chat Module)

## 개요
이 모듈은 Backand 의 Chat 진행 및 통찰 추출을 담당하는 LangGraph Graph입니다.

## 구조
```
chat/
├── modules/
│   ├── agents.py      # 에이전트 정의 (선택)
│   ├── conditions.py  # 조건부 로직 (선택)
│   ├── models.py      # LLM/모델 설정 (선택)
│   ├── nodes.py       # Graph 노드 클래스들 정의 (필수)
│   ├── prompts.py     # 프롬프트 템플릿 (선택)
│   ├── state.py       # 상태 정의 (필수)
│   ├── tools.py       # 도구 함수 (선택)
│   └── utils.py       # 유틸리티 함수 (선택)
├── pyproject.toml     # 패키지 메타데이터
├── README.md          # 본 문서
└── graph.py           # Graph 정의
```

## 사용 방법
```python
from casts.chat.graph import chat_graph

initial_state = {
    "query": "Hello, Act"
}

result = chat_graph().invoke(initial_state)
```

## 확장 방법
1. `modules/nodes.py`에 새 노드 클래스를 추가
2. 필요시 agents/conditions/tools/prompts/models 정의
3. `graph.py`에서 Graph에 연결

