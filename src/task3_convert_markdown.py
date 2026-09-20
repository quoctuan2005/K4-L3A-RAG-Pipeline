"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import json
from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def _write_non_empty_markdown(output_path: Path, content: str) -> None:
    if not content.strip():
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content.strip() + "\n", encoding="utf-8")


def convert_legal_docs() -> None:
    from markitdown import MarkItDown

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    if not legal_dir.exists():
        return

    converter = MarkItDown()
    for path in sorted(legal_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue

        result = converter.convert(str(path))
        output_path = output_dir / path.relative_to(legal_dir).with_suffix(".md")
        _write_non_empty_markdown(output_path, result.text_content)


def convert_news_articles() -> None:
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    if not news_dir.exists():
        return

    for path in sorted(news_dir.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        content = str(data.get("content_markdown") or "").strip()
        if not content:
            continue

        title = str(data.get("title") or path.stem).strip() or path.stem
        header = (
            f"# {title}\n\n"
            f"**Source:** {data.get('url', '')}\n\n"
            f"**Crawled:** {data.get('date_crawled', '')}\n\n---\n\n"
        )
        output_path = output_dir / path.relative_to(news_dir).with_suffix(".md")
        _write_non_empty_markdown(output_path, header + content)


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
