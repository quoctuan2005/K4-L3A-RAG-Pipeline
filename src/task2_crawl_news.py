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
from pathlib import Path


import html
import re
from datetime import datetime
from html.parser import HTMLParser
import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://vnexpress.net/cam-nang-du-lich-da-nang-4470111.html",
    "https://vnexpress.net/cam-nang-du-lich-phu-quoc-4106697.html",
    "https://vnexpress.net/cam-nang-du-lich-hoi-an-4446174.html",
    "https://vnexpress.net/cam-nang-du-lich-sa-pa-4108517.html",
    "https://vnexpress.net/cam-nang-du-lich-ha-long-4457134.html",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


class VnExpressMarkdownParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.output = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        if any(skip_cls in cls for skip_cls in ["box-related", "box-category", "box-header", "box-comment", "banner", "ads"]):
            self.skip = True
            return
        if tag in ["h2", "h3", "h4"]:
            prefix = "### " if tag == "h3" else ("#### " if tag == "h4" else "## ")
            self.output.append(f"\n\n{prefix}")
        elif tag == "p":
            self.output.append("\n\n")
        elif tag == "li":
            self.output.append("\n* ")
        elif tag == "br":
            self.output.append("\n")

    def handle_endtag(self, tag):
        if tag in ["div", "section", "aside"]:
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            text = data.strip()
            if text:
                self.output.append(data)


async def crawl_article(url: str) -> dict:
    """Crawl bài viết VnExpress và chuyển đổi sang Markdown sạch."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    raw_html = response.text

    # Trích xuất tiêu đề
    title_match = re.search(r'<h1[^>]*class="[^"]*title-detail[^"]*"[^>]*>(.*?)</h1>', raw_html, re.DOTALL)
    if not title_match:
        title_match = re.search(r'<title>(.*?)</title>', raw_html, re.DOTALL)
    title = html.unescape(re.sub(r"<[^>]+>", "", title_match.group(1)).strip()) if title_match else "Cẩm nang du lịch"
    title = title.split("- VnExpress")[0].strip()

    # Trích xuất mô tả / sapo
    desc_match = re.search(r'<p[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</p>', raw_html, re.DOTALL)
    desc = html.unescape(re.sub(r"<[^>]+>", "", desc_match.group(1)).strip()) if desc_match else ""

    # Trích xuất phần thân bài viết
    article_match = re.search(r'<article\b[^>]*class="[^"]*fck_detail[^"]*"[^>]*>(.*?)</article>', raw_html, re.DOTALL)
    body_html = article_match.group(1) if article_match else raw_html

    # Loại bỏ scripts, styles, comments
    body_html = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", body_html, flags=re.IGNORECASE)
    body_html = re.sub(r"<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>", "", body_html, flags=re.IGNORECASE)
    body_html = re.sub(r"<!--.*?-->", "", body_html, flags=re.DOTALL)

    parser = VnExpressMarkdownParser()
    parser.feed(body_html)
    raw_md = "".join(parser.output)

    # Lọc bỏ menu điều hướng, breadcrumb và khoảng trắng thừa
    cleaned_lines = []
    for line in raw_md.split("\n"):
        s = line.strip()
        if not s or s == "*" or s.startswith("* Trở lại") or s.startswith("* Điều hướng"):
            continue
        cleaned_lines.append(line)

    content_markdown = "\n".join(cleaned_lines)
    content_markdown = re.sub(r"\n{3,}", "\n\n", content_markdown).strip()

    if desc:
        content_markdown = f"**{desc}**\n\n{content_markdown}"

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": content_markdown,
    }


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
