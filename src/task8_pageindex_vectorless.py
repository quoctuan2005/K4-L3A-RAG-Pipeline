"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.

Chưa cấu hình PAGEINDEX_API_KEY thì ``pageindex_search`` trả list rỗng, Task 9
sẽ tiếp tục dùng hybrid result.
"""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fpdf import FPDF

from .task1_collect_legal_docs import find_unicode_font, markdown_to_plain_text
from .task4_chunking_indexing import parse_header


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

# Hai đường dẫn này đã có sẵn trong .gitignore.
CACHE_FILE = Path(__file__).parent.parent / "pageindex_doc_ids.json"
PDF_DIR = Path(__file__).parent.parent / "pageindex_pdfs"

# Dịch vụ ngoài: chặn cứng thời gian chờ để pipeline không treo.
POLL_INTERVAL_SECONDS = 2
RETRIEVAL_TIMEOUT_SECONDS = 30
UPLOAD_READY_TIMEOUT_SECONDS = 300


def _client():
    from pageindex import PageIndexClient

    if not PAGEINDEX_API_KEY:
        raise RuntimeError("Chưa cấu hình PAGEINDEX_API_KEY trong .env")
    return PageIndexClient(api_key=PAGEINDEX_API_KEY)


def load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def markdown_to_pdf(path: Path, target: Path) -> dict:
    """PageIndex nhận file PDF nên convert Markdown trước khi upload."""
    fields, body = parse_header(path.read_text(encoding="utf-8"))
    title = fields.get("title") or path.stem

    pdf = FPDF(format="A4")
    pdf.add_font("body", "", str(find_unicode_font()))
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("body", size=13)
    pdf.multi_cell(0, 7, title)
    pdf.ln(3)
    pdf.set_font("body", size=11)
    pdf.multi_cell(0, 6, markdown_to_plain_text(body))
    target.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(target))

    url = fields.get("source", "")
    return {
        "source": path.name,
        "title": title,
        "doc_type": fields.get("doc_type")
        or ("legal" if "legal" in path.parts else "news"),
        "url": None if url in {"", "N/A"} else url,
    }


def _extract(payload: dict, *names: str):
    """Lấy field đầu tiên khớp tên, tránh vỡ khi SDK đổi schema."""
    for name in names:
        if isinstance(payload, dict) and payload.get(name) is not None:
            return payload[name]
    return None


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    client = _client()
    cache = load_cache()

    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        key = path.relative_to(STANDARDIZED_DIR).as_posix()
        if key in cache:
            print(f"Skipped (đã upload): {key}")
            continue

        pdf_path = PDF_DIR / f"{path.stem}.pdf"
        metadata = markdown_to_pdf(path, pdf_path)
        response = client.submit_document(file_path=str(pdf_path))
        doc_id = _extract(response, "doc_id", "document_id", "id")
        if not doc_id:
            raise RuntimeError(f"Không đọc được doc_id từ response: {response}")

        cache[key] = {"doc_id": doc_id, "metadata": metadata}
        save_cache(cache)
        print(f"Uploaded: {key} -> {doc_id}")

    # Tài liệu cần thời gian index trước khi truy vấn được.
    deadline = time.time() + UPLOAD_READY_TIMEOUT_SECONDS
    for key, entry in cache.items():
        while time.time() < deadline:
            if client.is_retrieval_ready(entry["doc_id"]):
                print(f"Ready: {key}")
                break
            time.sleep(POLL_INTERVAL_SECONDS)
        else:
            print(f"Quá thời gian chờ index: {key}")


def _wait_for_retrieval(client, retrieval_id: str) -> dict:
    """Poll kết quả cho tới khi xong hoặc hết thời gian chờ."""
    deadline = time.time() + RETRIEVAL_TIMEOUT_SECONDS
    while time.time() < deadline:
        payload = client.get_retrieval(retrieval_id)
        status = str(_extract(payload, "status") or "completed").lower()
        if status in {"completed", "success", "done"}:
            return payload
        if status in {"failed", "error"}:
            raise RuntimeError(f"PageIndex retrieval lỗi: {payload}")
        time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError(f"PageIndex quá {RETRIEVAL_TIMEOUT_SECONDS}s không trả kết quả")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if top_k <= 0 or not PAGEINDEX_API_KEY:
        return []

    cache = load_cache()
    if not cache:
        return []

    client = _client()
    collected = []
    for entry in cache.values():
        submitted = client.submit_query(doc_id=entry["doc_id"], query=query)
        retrieval_id = _extract(submitted, "retrieval_id", "id")
        payload = (
            _wait_for_retrieval(client, retrieval_id) if retrieval_id else submitted
        )
        nodes = _extract(payload, "retrieved_nodes", "nodes", "results") or []
        for node in nodes:
            text = _extract(node, "text", "content", "node_text", "summary")
            if not text:
                continue
            collected.append(
                {
                    "text": str(text),
                    "score": _extract(node, "relevance_score", "score"),
                    "metadata": entry["metadata"],
                }
            )

    # API không đảm bảo có score; khi thiếu thì cho điểm giảm dần theo rank.
    collected.sort(key=lambda item: float(item["score"] or 0.0), reverse=True)
    results = []
    for index, item in enumerate(collected[:top_k]):
        results.append(
            {
                "id": f"pageindex::{item['metadata']['source']}::{index}",
                "content": item["text"],
                "score": float(item["score"]) if item["score"] else 1.0 / (index + 1),
                "metadata": {**item["metadata"], "chunk_index": index},
                "retrieval_method": "pageindex",
            }
        )
    return results


if __name__ == "__main__":
    upload_documents()
