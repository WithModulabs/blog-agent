"""Test the Chat graph.

Official document URL:
    https://docs.langchain.com/oss/python/langgraph/test"""

from __future__ import annotations

from casts.chat.graph import chat_graph


def test_graph_produces_result() -> None:
    graph = chat_graph()

    # 최소 상태로 그래프 실행
    result = graph.invoke({"query": "I'm joining Act"})

    # SampleNode가 result 키를 생성하는지 확인
    assert "result" in result
    assert result["result"] == "Welcome to the Act!"
