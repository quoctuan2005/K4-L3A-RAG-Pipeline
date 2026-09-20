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


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    # 1. Cẩm nang du lịch Đà Nẵng (25.900 ký tự: điểm vui chơi, bãi biển, ẩm thực mì Quảng/bánh tráng, khách sạn)
    "https://vnexpress.net/cam-nang-du-lich-da-nang-4470111.html",
    
    # 2. Cẩm nang du lịch Phú Quốc (17.600 ký tự: cáp treo, Safari, tour đảo, mùa lý tưởng, đặc sản bún quậy)
    "https://vnexpress.net/cam-nang-du-lich-phu-quoc-4106697.html",
    
    # 3. Cẩm nang du lịch Hội An (12.500 ký tự: phố cổ, đi thuyền sông Hoài, thả đèn hoa đăng, làng gốm, cao lầu)
    "https://vnexpress.net/cam-nang-du-lich-hoi-an-4446174.html",
    
    # 4. Cẩm nang du lịch Sa Pa (10.000 ký tự: đỉnh Fansipan, đèo Ô Quy Hồ, bản Cát Cát, mùa lúa chín, đồ nướng)
    "https://vnexpress.net/cam-nang-du-lich-sa-pa-4108517.html",
    
    # 5. Cẩm nang du lịch Hạ Long (13.700 ký tự: tour du thuyền, vịnh Bái Tử Long, chèo thuyền kayak, hang Sửng Sốt)
    "https://vnexpress.net/cam-nang-du-lich-ha-long-4457134.html",
]



async def crawl_article(url: str) -> dict:
    """Crawl nội dung bài viết từ URL và trả về dict theo contract."""
    from datetime import datetime
    import requests
    from bs4 import BeautifulSoup

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1. Tiêu đề
    title_tag = soup.find("h1", class_="title-detail") or soup.find("h1") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Cẩm nang du lịch"

    # 2. Nội dung bài viết
    article_body = (
        soup.find("article", class_="fck_detail")
        or soup.find("div", class_="fck_detail")
        or soup.find("article")
        or soup.find("body")
    )

    paragraphs = []
    description = soup.find("p", class_="description")
    if description:
        paragraphs.append(f"**{description.get_text(strip=True)}**\n")

    if article_body:
        for elem in article_body.find_all(["h2", "h3", "h4", "p"]):
            text = elem.get_text(strip=True)
            if not text:
                continue
            if elem.name == "h2":
                paragraphs.append(f"\n## {text}\n")
            elif elem.name == "h3":
                paragraphs.append(f"\n### {text}\n")
            elif elem.name == "h4":
                paragraphs.append(f"\n#### {text}\n")
            else:
                paragraphs.append(text)

    content_markdown = "\n\n".join(paragraphs).strip()

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
