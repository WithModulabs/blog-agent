"""State definitions for Blog Writer cast.

Defines InputState, OutputState, and OverallState (BlogState) according to CLAUDE.md spec.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, HttpUrl
from typing_extensions import TypedDict

# =============================================================================
# Configuration Enums
# =============================================================================


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENROUTER = "openrouter"


class ImageProvider(str, Enum):
    """Supported image generation providers."""

    DALLE = "dalle"
    STABILITY = "stability"
    UNSPLASH = "unsplash"
    PEXELS = "pexels"


class ScraperType(str, Enum):
    """Supported web scraping methods."""

    BEAUTIFULSOUP = "beautifulsoup"
    PLAYWRIGHT = "playwright"


class SearchProvider(str, Enum):
    """Supported web search providers."""

    TAVILY = "tavily"


# =============================================================================
# Configuration Schema
# =============================================================================


class BlogWriterConfig(BaseModel):
    """Configuration for Blog Writer cast."""

    llm_provider: LLMProvider = LLMProvider.OPENAI
    image_provider: ImageProvider = ImageProvider.DALLE
    scraper_type: ScraperType = ScraperType.BEAUTIFULSOUP


# =============================================================================
# API Request/Response Models (FastAPI)
# =============================================================================


class BlogRequest(BaseModel):
    """Input request model for Blog Writer API."""

    url: HttpUrl  # 참고할 웹사이트 URL
    user_keywords: Optional[list[str]] = None  # 사용자 지정 키워드 (선택)
    config: Optional[BlogWriterConfig] = None  # 설정 (선택)


class SEOMeta(BaseModel):
    """SEO metadata model."""

    title: str
    description: str


class BlogResponse(BaseModel):
    """Output response model for Blog Writer API."""

    html_content: str  # 이미지 포함 HTML 블로그
    suggested_keywords: list[str]  # 제안된 키워드 (최대 30개)
    selected_keywords: list[str]  # 선택된 키워드
    seo_meta: SEOMeta  # SEO 메타 정보
    image_urls: list[str]  # 생성된 이미지 URL들


# =============================================================================
# Graph State (LangGraph TypedDict)
# =============================================================================


class InputState(TypedDict):
    """Input state for the graph."""

    url: str
    user_keywords: Optional[list[str]]
    config: Optional[dict]


class OutputState(TypedDict):
    """Output state from the graph."""

    html_content: str
    suggested_keywords: list[str]
    selected_keywords: list[str]
    seo_meta: dict
    image_urls: list[str]


class BlogState(TypedDict, total=False):
    """Overall graph state container.

    Attributes:
        url: Source URL to scrape
        user_keywords: Optional user-provided keywords
        config: Configuration settings
        raw_content: Scraped web content
        analyzed_content: Analyzed/summarized content
        suggested_keywords: AI-suggested keywords (up to 30)
        selected_keywords: User-selected keywords
        search_results: Web search results for selected keywords
        blog_markdown: Generated blog in markdown
        image_urls: Generated/fetched image URLs
        html_content: Final HTML output
        seo_meta: SEO metadata (title, description)
    """

    # Input
    url: str
    user_keywords: Optional[list[str]]
    config: dict

    # Processing
    raw_content: str
    analyzed_content: dict
    suggested_keywords: list[str]
    selected_keywords: list[str]
    search_results: list[dict]
    blog_markdown: str
    image_urls: list[str]

    # Output
    html_content: str
    seo_meta: dict
