"""Node implementations for Blog Writer cast.

Implements 8 nodes as specified in CLAUDE.md:
- FetchContent: URL에서 웹 콘텐츠 수집
- AnalyzeContent: 핵심 내용 분석 및 요약
- SuggestKeywords: 키워드 최대 30개 제안
- HumanSelectKeywords: 사용자 키워드 선택 (interrupt)
- WriteBlog: 블로그 마크다운 작성
- OptimizeSEO: SEO 메타 정보 생성
- GenerateImages: 이미지 생성/수집
- ConvertToHTML: 최종 HTML 변환
"""

import json
import re

import markdown

from casts.base_node import AsyncBaseNode
from casts.blog_writer.modules.models import get_llm
from casts.blog_writer.modules.prompts import (
    ANALYZE_CONTENT_PROMPT,
    GENERATE_IMAGE_PROMPT,
    OPTIMIZE_SEO_PROMPT,
    SUGGEST_KEYWORDS_PROMPT,
    WRITE_BLOG_PROMPT,
)
from casts.blog_writer.modules.state import (
    ImageProvider,
    LLMProvider,
    ScraperType,
)
from casts.blog_writer.modules.tools import fetch_content, generate_image


class FetchContent(AsyncBaseNode):
    """URL에서 웹 콘텐츠 수집 (BS4/Playwright)."""

    async def execute(self, state, config=None):
        """웹 콘텐츠 수집."""
        url = state["url"]

        # Get scraper type from config
        scraper_type = ScraperType.BEAUTIFULSOUP
        if state.get("config"):
            scraper_type = ScraperType(
                state["config"].get("scraper_type", "beautifulsoup")
            )

        self.log(f"다음 URL에서 컨텐츠를 가져오는 중: {url} (스크레이퍼: {scraper_type})")

        raw_content = await fetch_content(url, scraper_type)

        # Limit content length to avoid token limits
        if len(raw_content) > 10000:
            raw_content = raw_content[:10000] + "\n...[truncated]"

        return {"raw_content": raw_content}


class AnalyzeContent(AsyncBaseNode):
    """핵심 내용 분석 및 요약."""

    async def execute(self, state, config=None):
        """콘텐츠 분석."""
        raw_content = state["raw_content"]

        # Get LLM provider from config
        llm_provider = LLMProvider.OPENAI
        if state.get("config"):
            llm_provider = LLMProvider(state["config"].get("llm_provider", "openai"))

        llm = get_llm(llm_provider)

        prompt = ANALYZE_CONTENT_PROMPT.format(raw_content=raw_content)

        self.log("컨텐츠 분석 중...")
        response = await llm.ainvoke(prompt)

        try:
            # Parse JSON from response
            content = response.content
            # Extract JSON from markdown code block if present
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
            if json_match:
                content = json_match.group(1)
            analyzed_content = json.loads(content)
        except json.JSONDecodeError:
            # Fallback structure
            analyzed_content = {
                "title": "Untitled",
                "main_topic": raw_content[:200],
                "key_points": [],
                "summary": raw_content[:500],
                "tone": "neutral",
            }

        return {"analyzed_content": analyzed_content}


class SuggestKeywords(AsyncBaseNode):
    """키워드 최대 30개 제안."""

    async def execute(self, state, config=None):
        """키워드 제안."""
        analyzed = state["analyzed_content"]
        user_keywords = state.get("user_keywords")

        # Get LLM provider from config
        llm_provider = LLMProvider.OPENAI
        if state.get("config"):
            llm_provider = LLMProvider(state["config"].get("llm_provider", "openai"))

        llm = get_llm(llm_provider)

        user_keywords_section = ""
        if user_keywords:
            user_keywords_section = (
                f"사용자 제공 키워드 참고: {', '.join(user_keywords)}"
            )

        prompt = SUGGEST_KEYWORDS_PROMPT.format(
            title=analyzed.get("title", ""),
            main_topic=analyzed.get("main_topic", ""),
            key_points=", ".join(analyzed.get("key_points", [])),
            summary=analyzed.get("summary", ""),
            user_keywords_section=user_keywords_section,
        )

        self.log("키워드 추천 중...")
        response = await llm.ainvoke(prompt)

        try:
            content = response.content
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
            if json_match:
                content = json_match.group(1)
            data = json.loads(content)
            suggested_keywords = data.get("keywords", [])[:30]
        except json.JSONDecodeError:
            # Fallback: extract any quoted words
            suggested_keywords = re.findall(r'"([^"]+)"', response.content)[:30]

        return {"suggested_keywords": suggested_keywords}


class HumanSelectKeywords(AsyncBaseNode):
    """사용자 키워드 선택 (interrupt).

    This node is configured as an interrupt point in the graph.
    User can modify/select keywords before proceeding.
    """

    async def execute(self, state, config=None):
        """키워드 선택 (기본: 제안된 키워드 모두 선택)."""
        suggested = state.get("suggested_keywords", [])

        # In interrupt mode, user can provide selected_keywords
        # If not provided (None), use all suggested keywords. Preserve empty list if explicitly provided.
        selected = state.get("selected_keywords")
        if selected is None:
            selected = suggested

        self.log(f"선택된 키워드: {selected}")

        return {"selected_keywords": selected}


class WriteBlog(AsyncBaseNode):
    """블로그 마크다운 작성."""

    async def execute(self, state, config=None):
        """블로그 글 작성."""
        analyzed = state["analyzed_content"]
        selected_keywords = state["selected_keywords"]

        llm_provider = LLMProvider.OPENAI
        if state.get("config"):
            llm_provider = LLMProvider(state["config"].get("llm_provider", "openai"))

        llm = get_llm(llm_provider)

        prompt = WRITE_BLOG_PROMPT.format(
            title=analyzed.get("title", ""),
            main_topic=analyzed.get("main_topic", ""),
            key_points=", ".join(analyzed.get("key_points", [])),
            summary=analyzed.get("summary", ""),
            selected_keywords=", ".join(selected_keywords),
        )

        self.log("블로그 포스트 작성 중...")
        response = await llm.ainvoke(prompt)

        return {"blog_markdown": response.content}


class OptimizeSEO(AsyncBaseNode):
    """SEO 메타 정보 생성."""

    async def execute(self, state, config=None):
        """SEO 최적화."""
        blog_markdown = state["blog_markdown"]
        selected_keywords = state["selected_keywords"]

        llm_provider = LLMProvider.OPENAI
        if state.get("config"):
            llm_provider = LLMProvider(state["config"].get("llm_provider", "openai"))

        llm = get_llm(llm_provider)

        prompt = OPTIMIZE_SEO_PROMPT.format(
            blog_markdown=blog_markdown[:3000],  # Limit for token budget
            selected_keywords=", ".join(selected_keywords),
        )

        self.log("SEO 최적화 중...")
        response = await llm.ainvoke(prompt)

        try:
            content = response.content
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
            if json_match:
                content = json_match.group(1)
            seo_meta = json.loads(content)
        except json.JSONDecodeError:
            seo_meta = {
                "title": "Blog Post",
                "description": blog_markdown[:160],
            }

        return {"seo_meta": seo_meta}


class GenerateImages(AsyncBaseNode):
    """이미지 생성/수집."""

    async def execute(self, state, config=None):
        """이미지 생성."""
        analyzed = state["analyzed_content"]

        # Get image provider from config
        image_provider = ImageProvider.DALLE
        if state.get("config"):
            image_provider = ImageProvider(
                state["config"].get("image_provider", "dalle")
            )

        llm_provider = LLMProvider.OPENAI
        if state.get("config"):
            llm_provider = LLMProvider(state["config"].get("llm_provider", "openai"))

        llm = get_llm(llm_provider)

        # Generate image prompt
        prompt = GENERATE_IMAGE_PROMPT.format(
            main_topic=analyzed.get("main_topic", ""),
            key_points=", ".join(analyzed.get("key_points", [])),
        )

        self.log("이미지 프롬프트 생성 중...")
        response = await llm.ainvoke(prompt)
        image_prompt = response.content.strip()

        self.log(f"{image_provider}를 사용하여 이미지 생성 중...")
        try:
            image_url = await generate_image(image_prompt, image_provider)
            image_urls = [image_url] if image_url else []
        except Exception as e:
            self.log(f"이미지 생성 실패: {e}")
            image_urls = []

        return {"image_urls": image_urls}


class ConvertToHTML(AsyncBaseNode):
    """최종 HTML 변환."""

    async def execute(self, state, config=None):
        """마크다운을 HTML로 변환."""
        blog_markdown = state["blog_markdown"]
        image_urls = state.get("image_urls", [])
        seo_meta = state.get("seo_meta", {})

        # Replace [IMAGE: description] placeholders with actual images
        if image_urls:

            def replace_image(match):
                if image_urls:
                    url = image_urls.pop(0)
                    description = match.group(1)
                    return f"![{description}]({url})"
                return match.group(0)

            blog_markdown = re.sub(
                r"\[IMAGE:\s*([^\]]+)\]", replace_image, blog_markdown
            )

        # Convert markdown to HTML
        html_body = markdown.markdown(
            blog_markdown, extensions=["extra", "codehilite", "tables"]
        )

        # Wrap with HTML template
        title = seo_meta.get("title", "Blog Post")
        description = seo_meta.get("description", "")

        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{description}">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.8;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
        }}
        h1 {{ color: #1a1a1a; margin-bottom: 1rem; }}
        h2 {{ color: #2a2a2a; margin-top: 2rem; }}
        img {{ max-width: 100%; height: auto; border-radius: 8px; margin: 1.5rem 0; }}
        p {{ margin: 1rem 0; }}
        code {{ background: #f4f4f4; padding: 0.2rem 0.4rem; border-radius: 4px; }}
        pre {{ background: #f4f4f4; padding: 1rem; border-radius: 8px; overflow-x: auto; }}
    </style>
</head>
<body>
    <article>
        {html_body}
    </article>
</body>
</html>"""

        return {"html_content": html_content}
