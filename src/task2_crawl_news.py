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

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://vnexpress.net/cam-nang-du-lich-da-nang-4470111.html",
    "https://vnexpress.net/cam-nang-du-lich-phu-quoc-4106697.html",
    "https://vnexpress.net/cam-nang-du-lich-hoi-an-4446174.html",
    "https://vnexpress.net/cam-nang-du-lich-sa-pa-4108517.html",
    "https://vnexpress.net/cam-nang-du-lich-ha-long-4457134.html",
]

# BYPASS để mỗi lần chạy lấy nội dung mới; chờ DOM tải xong trước khi đọc.
RUN_CONFIG = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    wait_until="domcontentloaded",
    page_timeout=60_000,
)


async def crawl_article(
    url: str,
    crawler: AsyncWebCrawler | None = None,
    css_selector: str | None = None,
) -> dict:
    """Crawl một bài viết và trả về dict theo schema của task 2.

    Truyền sẵn ``crawler`` để tái sử dụng một browser cho nhiều URL.
    ``css_selector`` giới hạn vùng nội dung, bỏ menu/sidebar của trang.
    """
    if crawler is None:
        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as owned:
            return await crawl_article(url, owned, css_selector)

    config = RUN_CONFIG.clone(css_selector=css_selector) if css_selector else RUN_CONFIG
    result = await crawler.arun(url=url, config=config)
    if not result.success:
        raise RuntimeError(result.error_message or "crawl failed")

    # crawl4ai trả về MarkdownGenerationResult; str() cho ra raw markdown.
    content_markdown = str(result.markdown).strip()
    if not content_markdown:
        raise RuntimeError("empty markdown")

    metadata = result.metadata or {}
    return {
        "url": url,
        "title": metadata.get("title") or "Unknown",
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": content_markdown,
    }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        for index, url in enumerate(ARTICLE_URLS, 1):
            try:
                article = await crawl_article(url, crawler)
                output = DATA_DIR / f"article_{index:02d}.json"
                output.write_text(
                    json.dumps(article, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                print(f"Saved: {output} — {article['title'][:60]}")
            except Exception as error:
                print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
