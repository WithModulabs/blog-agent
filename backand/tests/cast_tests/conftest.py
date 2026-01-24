"""Fixtures for Blog Writer tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_llm_response():
    """Mock LLM response factory."""

    def _create_response(content: str):
        mock = MagicMock()
        mock.content = content
        return mock

    return _create_response


@pytest.fixture
def mock_llm(mock_llm_response):
    """Mock LLM instance."""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value=mock_llm_response('{"test": "response"}'))
    return llm


@pytest.fixture
def sample_state():
    """Sample state for testing."""
    return {
        "url": "https://example.com/article",
        "user_keywords": None,
        "config": {
            "llm_provider": "openai",
            "image_provider": "dalle",
            "scraper_type": "beautifulsoup",
        },
    }


@pytest.fixture
def sample_analyzed_content():
    """Sample analyzed content for testing."""
    return {
        "title": "Test Article",
        "main_topic": "This is a test article about testing.",
        "key_points": ["Point 1", "Point 2", "Point 3"],
        "summary": "A comprehensive summary of the test article.",
        "tone": "technical",
    }


@pytest.fixture
def sample_blog_markdown():
    """Sample blog markdown for testing."""
    return """# Test Blog Post

## Introduction

This is a test blog post.

[IMAGE: Main illustration]

## Main Content

Here is the main content.

## Conclusion

Thank you for reading.
"""
