"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CACHE_FILE = Path(__file__).parent.parent / "data" / ".pageindex_cache.json"


def upload_documents() -> dict[str, str]:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    if not PAGEINDEX_API_KEY:
        return {}

    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    try:
        from pageindex import PageIndexClient
        client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
        doc_ids = {}
        for folder in ["legal", "news"]:
            target_dir = STANDARDIZED_DIR / folder
            if not target_dir.exists():
                continue
            for path in target_dir.glob("*.md"):
                try:
                    res = client.submit_document(file_path=str(path))
                    if isinstance(res, dict) and "document_id" in res:
                        doc_ids[path.name] = res["document_id"]
                except Exception as e:
                    print(f"Không thể upload {path.name}: {e}")
        CACHE_FILE.write_text(json.dumps(doc_ids, ensure_ascii=False, indent=2), encoding="utf-8")
        return doc_ids
    except Exception as e:
        print(f"Lỗi khởi tạo PageIndex: {e}")
        return {}


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if not PAGEINDEX_API_KEY or not query.strip():
        return []

    try:
        from pageindex import PageIndexClient
        client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
        doc_ids = upload_documents()
        if not doc_ids:
            return []
        
        # Gọi truy vấn nếu PageIndex có document_ids
        results = []
        # Return SearchResult formatted items
        return results[:top_k]
    except Exception:
        return []


if __name__ == "__main__":
    print(pageindex_search("du lịch", top_k=3))
