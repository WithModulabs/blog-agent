"""Test the Blog Writer nodes.

Tests each node in isolation with mocked dependencies.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from casts.blog_writer.modules.nodes import (
    AnalyzeContent,
    ConvertToHTML,
    FetchContent,
    GenerateImages,
    HumanSelectKeywords,
    OptimizeSEO,
    SuggestKeywords,
    WriteBlog,
)


class TestFetchContent:
    """Tests for FetchContent node."""

    @pytest.mark.asyncio
    async def test_fetch_content_beautifulsoup(self, sample_state):
        """Test content fetching with BeautifulSoup."""
        node = FetchContent()

        with patch(
            "casts.blog_writer.modules.nodes.fetch_content",
            new_callable=AsyncMock,
            return_value="Sample web content from the page",
        ):
            result = await node.execute(sample_state)

        assert "raw_content" in result
        assert isinstance(result["raw_content"], str)

    @pytest.mark.asyncio
    async def test_fetch_content_truncates_long_content(self, sample_state):
        """Test that long content is truncated."""
        node = FetchContent()
        long_content = "x" * 15000

        with patch(
            "casts.blog_writer.modules.nodes.fetch_content",
            new_callable=AsyncMock,
            return_value=long_content,
        ):
            result = await node.execute(sample_state)

        assert len(result["raw_content"]) < 15000
        assert "[truncated]" in result["raw_content"]


class TestAnalyzeContent:
    """Tests for AnalyzeContent node."""

    @pytest.mark.asyncio
    async def test_analyze_content_success(self, sample_state, mock_llm_response):
        """Test successful content analysis."""
        node = AnalyzeContent()
        sample_state["raw_content"] = "Sample raw content"

        mock_response = mock_llm_response("""{
            "title": "Test Title",
            "main_topic": "Main topic here",
            "key_points": ["Point 1", "Point 2"],
            "summary": "Summary text",
            "tone": "formal"
        }""")

        with patch("casts.blog_writer.modules.nodes.get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm

            result = await node.execute(sample_state)

        assert "analyzed_content" in result
        assert "title" in result["analyzed_content"]


class TestSuggestKeywords:
    """Tests for SuggestKeywords node."""

    @pytest.mark.asyncio
    async def test_suggest_keywords_up_to_thirty(
        self, sample_state, sample_analyzed_content, mock_llm_response
    ):
        """Test that keywords are suggested up to 30."""
        node = SuggestKeywords()
        sample_state["analyzed_content"] = sample_analyzed_content

        # Test Case 1: Exactly 30 keywords
        keywords_30 = [f"keyword{i}" for i in range(1, 31)]
        mock_response_30 = mock_llm_response(json.dumps({"keywords": keywords_30}))

        with patch("casts.blog_writer.modules.nodes.get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response_30)
            mock_get_llm.return_value = mock_llm
            result = await node.execute(sample_state)
            assert len(result["suggested_keywords"]) == 30

        # Test Case 2: Fewer than 30 keywords (e.g., 5)
        keywords_5 = [f"keyword{i}" for i in range(1, 6)]
        mock_response_5 = mock_llm_response(json.dumps({"keywords": keywords_5}))

        with patch("casts.blog_writer.modules.nodes.get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response_5)
            mock_get_llm.return_value = mock_llm
            result = await node.execute(sample_state)
            assert len(result["suggested_keywords"]) == 5

        # Test Case 3: More than 30 keywords (capped at 30)
        keywords_35 = [f"keyword{i}" for i in range(1, 36)]
        mock_response_35 = mock_llm_response(json.dumps({"keywords": keywords_35}))

        with patch("casts.blog_writer.modules.nodes.get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response_35)
            mock_get_llm.return_value = mock_llm
            result = await node.execute(sample_state)
            assert len(result["suggested_keywords"]) == 30


class TestHumanSelectKeywords:
    """Tests for HumanSelectKeywords node."""

    @pytest.mark.asyncio
    async def test_uses_suggested_when_no_selection(self, sample_state):
        """Test that suggested keywords are used when no selection made."""
        node = HumanSelectKeywords()
        sample_state["suggested_keywords"] = ["kw1", "kw2", "kw3"]

        result = await node.execute(sample_state)

        assert result["selected_keywords"] == ["kw1", "kw2", "kw3"]

    @pytest.mark.asyncio
    async def test_uses_user_selection(self, sample_state):
        """Test that user selection is preserved."""
        node = HumanSelectKeywords()
        sample_state["suggested_keywords"] = ["kw1", "kw2", "kw3"]
        sample_state["selected_keywords"] = ["kw1"]

        result = await node.execute(sample_state)

        assert result["selected_keywords"] == ["kw1"]


class TestWriteBlog:
    """Tests for WriteBlog node."""

    @pytest.mark.asyncio
    async def test_write_blog_generates_markdown(
        self, sample_state, sample_analyzed_content, mock_llm_response
    ):
        """Test blog writing generates markdown."""
        node = WriteBlog()
        sample_state["analyzed_content"] = sample_analyzed_content
        sample_state["selected_keywords"] = ["test", "blog", "writing"]

        mock_response = mock_llm_response("# Test Blog\n\nContent here...")

        with patch("casts.blog_writer.modules.nodes.get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm

            result = await node.execute(sample_state)

        assert "blog_markdown" in result
        assert "#" in result["blog_markdown"]


class TestOptimizeSEO:
    """Tests for OptimizeSEO node."""

    @pytest.mark.asyncio
    async def test_optimize_seo_generates_meta(
        self, sample_state, sample_blog_markdown, mock_llm_response
    ):
        """Test SEO optimization generates meta info."""
        node = OptimizeSEO()
        sample_state["blog_markdown"] = sample_blog_markdown
        sample_state["selected_keywords"] = ["test"]

        mock_response = mock_llm_response(
            '{"title": "SEO Title", "description": "SEO Description"}'
        )

        with patch("casts.blog_writer.modules.nodes.get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm

            result = await node.execute(sample_state)

        assert "seo_meta" in result
        assert "title" in result["seo_meta"]
        assert "description" in result["seo_meta"]


class TestGenerateImages:
    """Tests for GenerateImages node."""

    @pytest.mark.asyncio
    async def test_generate_images_returns_urls(
        self, sample_state, sample_analyzed_content, mock_llm_response
    ):
        """Test image generation returns URLs."""
        node = GenerateImages()
        sample_state["analyzed_content"] = sample_analyzed_content

        mock_response = mock_llm_response("A beautiful illustration of testing")

        with (
            patch("casts.blog_writer.modules.nodes.get_llm") as mock_get_llm,
            patch(
                "casts.blog_writer.modules.nodes.generate_image",
                new_callable=AsyncMock,
                return_value="https://example.com/image.png",
            ),
        ):
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm

            result = await node.execute(sample_state)

        assert "image_urls" in result
        assert isinstance(result["image_urls"], list)


class TestConvertToHTML:
    """Tests for ConvertToHTML node."""

    @pytest.mark.asyncio
    async def test_convert_to_html_generates_valid_html(
        self, sample_state, sample_blog_markdown
    ):
        """Test HTML conversion generates valid HTML."""
        node = ConvertToHTML()
        sample_state["blog_markdown"] = sample_blog_markdown
        sample_state["image_urls"] = ["https://example.com/image.png"]
        sample_state["seo_meta"] = {
            "title": "Test Title",
            "description": "Test description",
        }

        result = await node.execute(sample_state)

        assert "html_content" in result
        assert "<!DOCTYPE html>" in result["html_content"]
        assert "<html" in result["html_content"]
        assert "Test Title" in result["html_content"]

    @pytest.mark.asyncio
    async def test_convert_to_html_replaces_image_placeholders(
        self, sample_state, sample_blog_markdown
    ):
        """Test that [IMAGE:] placeholders are replaced with actual images."""
        node = ConvertToHTML()
        sample_state["blog_markdown"] = sample_blog_markdown
        sample_state["image_urls"] = ["https://example.com/test-image.png"]
        sample_state["seo_meta"] = {"title": "Test", "description": "Desc"}

        result = await node.execute(sample_state)

        assert "https://example.com/test-image.png" in result["html_content"]
        assert "[IMAGE:" not in result["html_content"]
