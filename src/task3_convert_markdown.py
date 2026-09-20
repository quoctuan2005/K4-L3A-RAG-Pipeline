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

Mỗi Markdown mở đầu bằng header trỏ ngược về file landing và URL công khai,
để đối chiếu được nội dung đã chuẩn hóa với nguồn gốc.
"""

import json
from datetime import datetime
from pathlib import Path

from markitdown import MarkItDown

from src.task1_collect_legal_docs import LEGAL_SOURCES


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

DOC_EXTENSIONS = {".pdf", ".doc", ".docx"}
MIN_CONTENT_CHARS = 200


def build_header(
    title: str,
    url: str | None,
    landing_file: str,
    doc_type: str,
    retrieved_at: str,
) -> str:
    """Header chung cho mọi Markdown, giữ đường dẫn ngược về nguồn."""
    return (
        f"# {title}\n\n"
        f"**Source:** {url or 'N/A'}\n\n"
        f"**Landing file:** {landing_file}\n\n"
        f"**Doc type:** {doc_type}\n\n"
        f"**Retrieved:** {retrieved_at}\n\n"
        "---\n\n"
    )


def write_markdown(output: Path, header: str, body: str) -> bool:
    """Ghi file Markdown, bỏ qua khi nội dung quá ngắn."""
    body = body.strip()
    if len(body) < MIN_CONTENT_CHARS:
        print(f"Bỏ qua (nội dung {len(body)} ký tự): {output.name}")
        return False
    # Ghi đè theo tên file cố định nên chạy lại không sinh bản sao.
    output.write_text(header + body + "\n", encoding="utf-8")
    print(f"Saved: {output.relative_to(OUTPUT_DIR.parent)} ({len(body)} ký tự)")
    return True


def convert_legal_docs() -> None:
    """Convert PDF/DOCX vào standardized/legal."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata_by_filename = {item["filename"]: item for item in LEGAL_SOURCES}
    converter = MarkItDown()

    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() not in DOC_EXTENSIONS:
            continue

        source = metadata_by_filename.get(path.name, {})
        title = source.get("title") or path.stem
        url = source.get("page_url")

        body = converter.convert(str(path)).text_content
        retrieved_at = datetime.fromtimestamp(path.stat().st_mtime).isoformat()

        header = build_header(title, url, path.name, "legal", retrieved_at)
        write_markdown(output_dir / f"{path.stem}.md", header, body)


def convert_news_articles() -> None:
    """Convert JSON vào standardized/news."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(news_dir.glob("*.json")):
        article = json.loads(path.read_text(encoding="utf-8"))
        header = build_header(
            article["title"],
            article["url"],
            path.name,
            "news",
            article["date_crawled"],
        )
        write_markdown(output_dir / f"{path.stem}.md", header, article["content_markdown"])


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
