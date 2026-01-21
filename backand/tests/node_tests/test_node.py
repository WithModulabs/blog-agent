"""Test the nodes for the Sam graph.

Official document URL: https://docs.langchain.com/oss/python/langgraph/test"""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage
from casts.chat.modules.nodes import AsyncSampleNode, SampleNode


def test_base_node_calls_execute() -> None:
    node = SampleNode()
    result = node({"messages": []})
    assert result == {"messages": [AIMessage(content="Welcome to the Act! by Sync Node")]}


@pytest.mark.asyncio
async def test_async_base_node_calls_execute() -> None:
    node = AsyncSampleNode()
    result = await node({"messages": []})
    assert result == {"messages": [AIMessage(content="Welcome to the Act! by Async Node")]}
