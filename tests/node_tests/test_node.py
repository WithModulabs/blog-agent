"""Test the nodes for the Sam graph.

Official document URL: https://docs.langchain.com/oss/python/langgraph/test"""

from __future__ import annotations

import pytest

from casts.chat.modules.nodes import AsyncSampleNode, SampleNode


def test_base_node_calls_execute() -> None:
    node = SampleNode()
    result = node({"query": "test"})
    assert result == {"result": "Welcome to the Act!"}


@pytest.mark.asyncio
async def test_async_base_node_calls_execute() -> None:
    node = AsyncSampleNode()
    result = await node({"query": "test"})
    assert result == {"result": "Welcome to the Act!"}
