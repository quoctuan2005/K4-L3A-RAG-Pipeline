"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import hashlib
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
PAGEINDEX_CACHE = STANDARDIZED_DIR.parent / "pageindex_documents.json"


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower(), flags=re.UNICODE))


def _stable_document_id(source: str) -> str:
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
    return f"local-{digest}"


def _load_chunks() -> list[dict]:
    from .task4_chunking_indexing import chunk_documents, load_documents

    return chunk_documents(load_documents())


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    STANDARDIZED_DIR.parent.mkdir(parents=True, exist_ok=True)

    mapping = {}
    if STANDARDIZED_DIR.exists():
        for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
            if not path.is_file() or not path.read_text(encoding="utf-8").strip():
                continue

            source = path.relative_to(STANDARDIZED_DIR).as_posix()
            mapping[source] = _stable_document_id(source)

    PAGEINDEX_CACHE.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if top_k <= 0 or not query.strip():
        return []

    if not PAGEINDEX_CACHE.exists():
        upload_documents()

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    scored = []
    for chunk in _load_chunks():
        content_tokens = _tokenize(chunk["content"])
        overlap = len(query_tokens & content_tokens)
        if overlap <= 0:
            continue

        coverage = overlap / max(len(query_tokens), 1)
        score = coverage + overlap / max(len(content_tokens), 1)
        scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = []
    for rank, (score, chunk) in enumerate(scored[:top_k], 1):
        results.append(
            {
                "id": f"pageindex::{chunk['id']}",
                "content": chunk["content"],
                "score": float(score) if score > 0 else 1.0 / rank,
                "metadata": chunk["metadata"],
                "retrieval_method": "pageindex",
            }
        )
    return results


if __name__ == "__main__":
    upload_documents()
