import asyncio
import json
import os

# Set up PYTHONPATH
import sys

sys.path.append(os.getcwd())

from unittest.mock import AsyncMock, MagicMock, patch

from casts.blog_writer.graph import blog_writer_graph


async def run_demo():
    print("🚀 블로그 글 작성기 데모 실행 시작 (MOCKED)...")

    # Initialize the graph
    app = blog_writer_graph.build()

    # Sample input
    inputs = {"url": "https://www.google.com", "user_keywords": ["AI", "Automation"]}

    # Mock LLM to avoid API key requirement
    mock_response = MagicMock()
    # Generate 30 keywords as if it came from the LLM
    keywords = [f"추천태그_{i}" for i in range(1, 31)]
    mock_response.content = json.dumps({"keywords": keywords})

    # Mocking get_llm which is used inside the nodes
    with (
        patch("casts.blog_writer.modules.nodes.get_llm") as mock_get_llm,
        patch(
            "casts.blog_writer.modules.nodes.fetch_content", new_callable=AsyncMock
        ) as mock_fetch,
    ):
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm.return_value = mock_llm
        mock_fetch.return_value = "Sample content for testing"

        # Run until the interrupt (human_select_keywords)
        print("⏳ 키워드 선택 단계까지 그래프 실행 중...")
        async for event in app.astream(inputs, stream_mode="updates"):
            for node_name, output in event.items():
                print(f"✅ '{node_name}' 노드 완료.")
                if node_name == "suggest_keywords":
                    keywords = output.get("suggested_keywords", [])
                    print(f"\n📊 추천된 키워드 (총 {len(keywords)}개):")
                    for i, kw in enumerate(keywords, 1):
                        print(f"  {i}. {kw}")

                    if len(keywords) >= 30:
                        print("\n🎉 성공: 30개의 키워드가 성공적으로 생성되었습니다!")
                    else:
                        print(f"\n⚠️ 경고: {len(keywords)}개의 키워드만 생성되었습니다.")

    print("\n🏁 데모가 성공적으로 완료되었습니다 (인터럽트 지점에서 정지).")


if __name__ == "__main__":
    asyncio.run(run_demo())
