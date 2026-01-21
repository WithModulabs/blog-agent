"""Tools for Blog Writer cast.

Includes web scraping and image generation/fetching tools.
"""

import os

import httpx
from bs4 import BeautifulSoup

from casts.blog_writer.modules.state import ImageProvider, ScraperType

# =============================================================================
# Web Scraping Tools
# =============================================================================


async def fetch_with_beautifulsoup(url: str) -> str:
    """Fetch web content using BeautifulSoup + httpx.

    Args:
        url: URL to fetch

    Returns:
        Extracted text content from the page
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script and style elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    # Get text content
    text = soup.get_text(separator="\n", strip=True)

    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


async def fetch_with_playwright(url: str) -> str:
    """Fetch web content using Playwright (for JS-rendered pages).

    Args:
        url: URL to fetch

    Returns:
        Extracted text content from the page
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, wait_until="networkidle")

        # Get main content
        content = await page.content()
        await browser.close()

    soup = BeautifulSoup(content, "html.parser")

    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


async def fetch_content(
    url: str, scraper_type: ScraperType = ScraperType.BEAUTIFULSOUP
) -> str:
    """Fetch web content using configured scraper.

    Args:
        url: URL to fetch
        scraper_type: Which scraper to use

    Returns:
        Extracted text content
    """
    if scraper_type == ScraperType.PLAYWRIGHT:
        return await fetch_with_playwright(url)
    return await fetch_with_beautifulsoup(url)


# =============================================================================
# Image Generation/Fetching Tools
# =============================================================================


async def generate_image_dalle(prompt: str, size: str = "1024x1024") -> str:
    """Generate image using OpenAI DALL-E.

    Args:
        prompt: Image generation prompt
        size: Image size

    Returns:
        Generated image URL
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        n=1,
    )
    return response.data[0].url


async def generate_image_stability(prompt: str) -> str:
    """Generate image using Stability AI.

    Args:
        prompt: Image generation prompt

    Returns:
        Generated image URL or base64 data
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image",
            headers={
                "Authorization": f"Bearer {os.getenv('STABILITY_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
            },
        )
        response.raise_for_status()
        data = response.json()
        # Return base64 image data (would need to be uploaded/converted)
        return f"data:image/png;base64,{data['artifacts'][0]['base64']}"


async def fetch_image_unsplash(query: str) -> str:
    """Fetch image from Unsplash.

    Args:
        query: Search query

    Returns:
        Image URL from Unsplash
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.unsplash.com/photos/random",
            params={"query": query, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {os.getenv('UNSPLASH_ACCESS_KEY')}"},
        )
        response.raise_for_status()
        data = response.json()
        return data["urls"]["regular"]


async def fetch_image_pexels(query: str) -> str:
    """Fetch image from Pexels.

    Args:
        query: Search query

    Returns:
        Image URL from Pexels
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": 1},
            headers={"Authorization": os.getenv("PEXELS_API_KEY")},
        )
        response.raise_for_status()
        data = response.json()
        if data["photos"]:
            return data["photos"][0]["src"]["large"]
        return ""


def _get_available_image_provider(requested_provider: ImageProvider) -> ImageProvider:
    """Determine available image provider based on API keys.

    Priority: Requested -> DALL-E -> Unsplash -> Pexels -> Stability
    """
    if requested_provider == ImageProvider.DALLE and os.getenv("OPENAI_API_KEY"):
        return ImageProvider.DALLE
    if requested_provider == ImageProvider.UNSPLASH and os.getenv(
        "UNSPLASH_ACCESS_KEY"
    ):
        return ImageProvider.UNSPLASH
    if requested_provider == ImageProvider.PEXELS and os.getenv("PEXELS_API_KEY"):
        return ImageProvider.PEXELS
    if requested_provider == ImageProvider.STABILITY and os.getenv("STABILITY_API_KEY"):
        return ImageProvider.STABILITY

    # Fallback cascade
    if os.getenv("OPENAI_API_KEY"):
        return ImageProvider.DALLE
    if os.getenv("UNSPLASH_ACCESS_KEY"):
        return ImageProvider.UNSPLASH
    if os.getenv("PEXELS_API_KEY"):
        return ImageProvider.PEXELS
    if os.getenv("STABILITY_API_KEY"):
        return ImageProvider.STABILITY

    return requested_provider


async def generate_image(
    prompt: str,
    provider: ImageProvider = ImageProvider.DALLE,
) -> str:
    """Generate or fetch image using configured provider with fallback support.

    Args:
        prompt: Image description/query
        provider: Image provider to use

    Returns:
        Image URL
    """
    active_provider = _get_available_image_provider(provider)

    if active_provider == ImageProvider.DALLE:
        return await generate_image_dalle(prompt)
    elif active_provider == ImageProvider.STABILITY:
        return await generate_image_stability(prompt)
    elif active_provider == ImageProvider.UNSPLASH:
        return await fetch_image_unsplash(prompt)
    elif active_provider == ImageProvider.PEXELS:
        return await fetch_image_pexels(prompt)
    else:
        # If no keys found at all, skip image generation gracefully
        # The node level handles this by catching exceptions
        raise ValueError(
            f"No API keys available for any image provider. Tried falling back from {provider}."
        )
