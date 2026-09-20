"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Chủ đề nhóm: Du lịch Việt Nam — chính sách và hướng dẫn cho khách du lịch.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.

Lưu ý: một số văn bản ký số chỉ là bản scan, không có text layer. Với các file
đó, script crawl toàn văn từ trang công bố rồi render lại thành PDF có text
layer, nên data/landing/legal/ luôn chỉ chứa PDF/DOC/DOCX đúng như đề bài.
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path

import requests
from fpdf import FPDF
from pdfminer.high_level import extract_text

from src.task2_crawl_news import crawl_article


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
# Bản chép tay cho văn bản scan mà trang công bố không đăng toàn văn.
TRANSCRIPT_DIR = Path(__file__).parent.parent / "data" / "transcripts"

# Mỗi tài liệu giữ cả trang công bố (để trích dẫn) và link PDF (để tải).
LEGAL_SOURCES = [
    {
        "filename": "cong-van-1560-vpcp-kgvx-chuong-trinh-phat-trien-du-lich-2021-2026.pdf",
        "title": (
            "Công văn số 1560/VPCP-KGVX của Văn phòng Chính phủ: "
            "V/v Chương trình phát triển du lịch Việt Nam giai đoạn 2021-2026"
        ),
        "page_url": "https://vanban.chinhphu.vn/?pageid=27160&docid=205462",
        "pdf_url": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2022/03/1560-kgvx.signed.pdf",
        # File ký số là bản scan 1 trang và trang công bố chỉ đăng metadata, nên
        # toàn văn được chép lại thủ công từ ảnh scan vào data/transcripts/.
        "content_selector": None,
        "page_has_full_text": False,
        "transcript": "cong-van-1560-vpcp-kgvx-chuong-trinh-phat-trien-du-lich-2021-2026.txt",
    },
    {
        "filename": "tcvn-13259-2020-du-lich-cong-dong-yeu-cau-chat-luong-dich-vu.pdf",
        "title": (
            "TCVN 13259:2020 — Du lịch cộng đồng: Yêu cầu về chất lượng dịch vụ"
        ),
        "page_url": "https://vietnamtourism.gov.vn/docs/925",
        "pdf_url": "https://vietnamtourism.gov.vn/docs/download/925",
        # PDF có text layer nên không cần crawl.
        # Thay cho Công văn 1560/VPCP-KGVX: file ký số đó là bản scan và trang
        # vanban.chinhphu.vn chỉ đăng metadata, không có toàn văn.
        "content_selector": None,
        "page_has_full_text": False,
    },
    {
        "filename": "quyet-dinh-147-qd-ttg-chien-luoc-phat-trien-du-lich-den-2030.pdf",
        "title": (
            "Quyết định 147/QĐ-TTg phê duyệt Chiến lược phát triển "
            "du lịch Việt Nam đến năm 2030"
        ),
        "page_url": "https://vietnamtourism.gov.vn/docs/908",
        "pdf_url": "https://vietnamtourism.gov.vn/docs/download/908",
        # PDF có text layer nên không cần crawl.
        "content_selector": None,
        "page_has_full_text": False,
    },
    {
        "filename": "nghi-quyet-bo-chinh-tri-du-lich-mui-nhon.pdf",
        "title": (
            "Nghị quyết Bộ Chính trị về phát triển du lịch Việt Nam "
            "trở thành ngành kinh tế mũi nhọn trong kỷ nguyên mới"
        ),
        "page_url": (
            "https://tulieuvankien.dangcongsan.vn/tin-hoat-dong/"
            "nghi-quyet-cua-bo-chinh-tri-ve-phat-trien-du-lich-viet-nam-tro-thanh-"
            "nganh-kinh-te-mui-nhon-trong-ky-nguyen-moi.html"
        ),
        "pdf_url": (
            "https://tulieuvankien.dangcongsan.vn/upload/2006988/20260827/"
            "nqtw26_signed_49491.pdf"
        ),
        # PDF là bản scan nhưng trang công bố có toàn văn trong div.article-content.
        "content_selector": "div.article-content",
        "page_has_full_text": True,
    },
]


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải ít nhất 3 PDF/DOCX từ nguồn công khai."""
    for source in LEGAL_SOURCES:
        target = DATA_DIR / source["filename"]
        if target.exists():
            print(f"Skipped (đã có): {target.name}")
            continue
        try:
            response = requests.get(
                source["pdf_url"],
                timeout=60,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            target.write_bytes(response.content)
            print(f"Saved: {target.name} ({len(response.content)} bytes)")
        except requests.RequestException as error:
            print(f"Failed: {source['pdf_url']} — {error}")


# Font Unicode để render tiếng Việt; fpdf2 không kèm sẵn font nào có dấu.
FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/Library/Fonts/Arial.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
]


def find_unicode_font() -> Path:
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Không tìm thấy font Unicode để render tiếng Việt. "
        "Thêm đường dẫn .ttf vào FONT_CANDIDATES."
    )


def markdown_to_plain_text(markdown: str) -> str:
    """Bỏ cú pháp Markdown, giữ lại phần chữ để đưa vào PDF."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", markdown)      # ảnh
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)       # link -> nhãn
    text = re.sub(r"[*_`]+", "", text)                          # nhấn mạnh
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)  # heading
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Token quá dài (URL còn sót) làm fpdf2 không xuống dòng được.
    text = re.sub(r"\S{60,}", lambda m: " ".join(re.findall(r".{1,60}", m.group())), text)
    return text.strip()


def render_text_pdf(
    source: dict,
    article: dict,
    target: Path,
    origin: str = "bản dựng lại từ trang công bố",
) -> None:
    """Render toàn văn thu được thành PDF có text layer."""
    pdf = FPDF(format="A4")
    pdf.add_font("body", "", str(find_unicode_font()))
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Ghi rõ đây là bản dựng lại từ trang công bố, không phải file ký số gốc.
    pdf.set_font("body", size=9)
    pdf.multi_cell(
        0,
        5,
        f"[{origin} phục vụ xử lý dữ liệu — không phải file ký số gốc]\n"
        f"Nguồn: {article['url']}\n"
        f"Bản gốc ký số (scan): {source['pdf_url']}\n"
        f"Ngày lấy nội dung: {article['date_crawled']}",
    )
    pdf.ln(4)

    pdf.set_font("body", size=13)
    pdf.multi_cell(0, 7, source["title"])
    pdf.ln(3)

    pdf.set_font("body", size=11)
    pdf.multi_cell(0, 6, markdown_to_plain_text(article["content_markdown"]))
    pdf.output(str(target))


def has_text_layer(path: Path, min_chars: int = 200) -> bool:
    """True nếu PDF trích được text; False với bản scan ảnh."""
    try:
        text = extract_text(str(path), maxpages=3) or ""
    except Exception as error:
        print(f"Không đọc được {path.name} — {error}")
        return False
    return len(text.strip()) >= min_chars


async def backfill_scanned_documents() -> None:
    """Thay PDF scan bằng bản text dựng từ trang công bố.

    Chạy lại an toàn: bản render đã có text layer nên lần sau sẽ được bỏ qua.
    """
    for source in LEGAL_SOURCES:
        pdf_path = DATA_DIR / source["filename"]
        if not pdf_path.exists():
            continue
        if has_text_layer(pdf_path):
            print(f"OK (có text layer): {pdf_path.name}")
            continue

        transcript = TRANSCRIPT_DIR / source.get("transcript", "")
        if source.get("transcript") and transcript.exists():
            article = {
                "url": source["page_url"],
                "title": source["title"],
                "date_crawled": datetime.now().isoformat(),
                "content_markdown": transcript.read_text(encoding="utf-8"),
            }
            render_text_pdf(source, article, pdf_path, origin="bản chép lại từ ảnh scan")
            print(f"Rendered từ transcript: {pdf_path.name}")
            continue

        if not source["page_has_full_text"]:
            print(
                f"THIẾU NỘI DUNG: {pdf_path.name} là bản scan và trang công bố "
                f"không có toàn văn → cần đổi nguồn khác."
            )
            continue

        print(f"Scan-only: {pdf_path.name} → crawl {source['page_url']}")
        try:
            article = await crawl_article(
                source["page_url"], css_selector=source["content_selector"]
            )
        except Exception as error:
            print(f"Failed: {source['page_url']} — {error}")
            continue

        # Giữ tiêu đề văn bản đã xác minh thay vì <title> của trang.
        article["title"] = source["title"]
        article["date_crawled"] = datetime.now().isoformat()
        render_text_pdf(source, article, pdf_path)
        print(
            f"Rendered: {pdf_path.name} "
            f"({len(article['content_markdown'])} chars, {pdf_path.stat().st_size} bytes)"
        )


if __name__ == "__main__":
    setup_directory()
    download_documents()
    asyncio.run(backfill_scanned_documents())
