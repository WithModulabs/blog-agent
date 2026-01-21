import asyncio
import json
import os

# Set up PYTHONPATH
import sys

sys.path.append(os.getcwd())

from unittest.mock import AsyncMock, MagicMock, patch

from casts.blog_writer.graph import blog_writer_graph


async def run_demo():
    print("🚀 Starting Blog Writer Demo Run (MOCKED)...")

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
        print("⏳ Running graph until keyword selection...")
        async for event in app.astream(inputs, stream_mode="updates"):
            for node_name, output in event.items():
                print(f"✅ Node '{node_name}' completed.")
                if node_name == "suggest_keywords":
                    keywords = output.get("suggested_keywords", [])
                    print(f"\n📊 Suggested Keywords ({len(keywords)} total):")
                    for i, kw in enumerate(keywords, 1):
                        print(f"  {i}. {kw}")

                    if len(keywords) >= 30:
                        print("\n🎉 SUCCESS: Successfully generated 30 keywords!")
                    else:
                        print(f"\n⚠️ WARNING: Only generated {len(keywords)} keywords.")

    print("\n🏁 Demo completed successfully (stopped at interrupt).")


if __name__ == "__main__":
    asyncio.run(run_demo())
