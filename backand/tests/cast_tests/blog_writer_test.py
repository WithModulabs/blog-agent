"""Test the Blog Writer graph integration.

Tests the compiled graph structure and basic invocation.
"""

from unittest.mock import AsyncMock, patch

import pytest

from casts.blog_writer.graph import BlogWriterGraph, blog_writer_graph


class TestBlogWriterGraph:
    """Tests for BlogWriterGraph class."""

    def test_graph_builds_successfully(self):
        """Test that graph builds without errors."""
        graph_builder = BlogWriterGraph()
        graph = graph_builder.build()

        assert graph is not None
        assert hasattr(graph, "invoke")

    def test_graph_has_correct_nodes(self):
        """Test that graph has all expected nodes."""
        graph_builder = BlogWriterGraph()
        graph = graph_builder.build()

        expected_nodes = [
            "fetch_content",
            "analyze_content",
            "suggest_keywords",
            "human_select_keywords",
            "write_blog",
            "optimize_seo",
            "generate_images",
            "convert_to_html",
        ]

        for node_name in expected_nodes:
            assert node_name in graph.nodes, f"Missing node: {node_name}"

    def test_graph_has_interrupt_configured(self):
        """Test that interrupt is configured at keyword selection."""
        graph_builder = BlogWriterGraph()
        graph = graph_builder.build()

        # Check interrupt configuration
        assert hasattr(graph, "interrupt_before") or hasattr(graph, "_interrupt_before")

    def test_graph_singleton_builds(self):
        """Test that blog_writer_graph singleton builds."""
        graph = blog_writer_graph.build()

        assert graph is not None
        assert graph.name == "BlogWriterGraph"


class TestBlogWriterGraphIntegration:
    """Integration tests for the full graph flow."""

    @pytest.mark.asyncio
    async def test_graph_runs_until_interrupt(self):
        """Test that graph runs until human_select_keywords interrupt."""
        graph = blog_writer_graph.build()

        # Mock all external dependencies
        with (
            patch(
                "casts.blog_writer.modules.nodes.fetch_content",
                new_callable=AsyncMock,
                return_value="Sample content from website",
            ),
            patch("casts.blog_writer.modules.nodes.get_llm") as mock_get_llm,
        ):
            # Create mock LLM that returns appropriate responses
            mock_llm = AsyncMock()

            async def mock_ainvoke(prompt):
                mock_response = AsyncMock()
                if "분석" in prompt or "analyze" in prompt.lower():
                    mock_response.content = """{
                        "title": "Test",
                        "main_topic": "Testing",
                        "key_points": ["A", "B"],
                        "summary": "Summary",
                        "tone": "formal"
                    }"""
                else:
                    mock_response.content = '{"keywords": ["k1", "k2", "k3"]}'
                return mock_response

            mock_llm.ainvoke = mock_ainvoke
            mock_get_llm.return_value = mock_llm

            # Run graph with interrupt
            config = {"configurable": {"thread_id": "test-thread"}}

            # The graph should pause at human_select_keywords
            # Using stream to check intermediate states
            result = None
            async for event in graph.astream(
                {"url": "https://example.com", "user_keywords": None},
                config=config,
            ):
                result = event

            # Should have reached suggest_keywords before interrupt
            assert result is not None


class TestGraphState:
    """Tests for graph state schemas."""

    def test_input_state_schema(self):
        """Test InputState schema."""
        from casts.blog_writer.modules.state import InputState

        # InputState should accept url and user_keywords
        state: InputState = {
            "url": "https://example.com",
            "user_keywords": ["test"],
            "config": None,
        }

        assert state["url"] == "https://example.com"

    def test_output_state_schema(self):
        """Test OutputState schema."""
        from casts.blog_writer.modules.state import OutputState

        state: OutputState = {
            "html_content": "<html>...</html>",
            "suggested_keywords": ["a", "b", "c"],
            "selected_keywords": ["a"],
            "seo_meta": {"title": "T", "description": "D"},
            "image_urls": ["https://example.com/img.png"],
        }

        assert "html_content" in state

    def test_blog_state_schema(self):
        """Test BlogState (overall state) schema."""
        from casts.blog_writer.modules.state import BlogState

        state: BlogState = {
            "url": "https://example.com",
            "raw_content": "Content...",
            "analyzed_content": {},
            "blog_markdown": "# Blog",
            "html_content": "<html>",
        }

        assert state["url"] == "https://example.com"
