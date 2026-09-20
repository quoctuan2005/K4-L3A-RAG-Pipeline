"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://vnexpress.net/cam-nang-du-lich-da-nang-4470111.html",
    "https://vnexpress.net/cam-nang-du-lich-phu-quoc-4106697.html",
    "https://vnexpress.net/cam-nang-du-lich-hoi-an-4446174.html",
    "https://vnexpress.net/cam-nang-du-lich-sa-pa-4108517.html",
    "https://vnexpress.net/cam-nang-du-lich-ha-long-4457134.html",
]


def _article_from_result(url: str, result: object) -> dict:
    metadata = getattr(result, "metadata", {}) or {}

    return {
        "url": url,
        "title": metadata.get("title", "Unknown"),
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": getattr(result, "markdown", "") or "",
    }


async def crawl_article(url: str) -> dict:
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return _article_from_result(url, result)


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
