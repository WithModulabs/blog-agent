"""Utility and Tool API endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Query

from api.schemas.blog import ScraperType, ImageProvider
from casts.blog_writer.modules import tools

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/scrape")
async def scrape_url(
    url: str = Query(..., description="URL to scrape"),
    type: ScraperType = Query(ScraperType.BEAUTIFULSOUP, description="Scraper type")
):
    """Scrape content from a URL directly."""
    try:
        content = await tools.fetch_content(url, type)
        return {"url": url, "content": content}
    except Exception as e:
        logger.exception("Scraping failed for url=%s", url)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/search")
async def search_images(
    query: str = Query(..., description="Search query"),
    provider: ImageProvider = Query(ImageProvider.UNSPLASH, description="Image provider")
):
    """Search or generate images directly."""
    try:
        image_url = await tools.generate_image(query, provider)
        return {"query": query, "provider": provider, "url": image_url}
    except Exception as e:
        logger.exception("Image search failed for query=%s", query)
        raise HTTPException(status_code=500, detail=str(e))
