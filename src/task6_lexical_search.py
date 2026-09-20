"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import re


CORPUS: list[dict] = []


def tokenize(text: str) -> list[str]:
    """Tách từ theo ký tự chữ/số.

    Dấu câu dính vào từ (``du lịch,``) sẽ làm lệch match nếu chỉ split khoảng
    trắng; ``\\w+`` giữ được dấu tiếng Việt.
    """
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def load_corpus() -> list[dict]:
    """Lấy đúng corpus chunks đã index ở Task 4 từ ChromaDB.

    Đọc ngược từ collection thay vì chunk lại để BM25 và dense chắc chắn
    dùng chung một tập chunk và một tập ID.
    """
    from .task4_chunking_indexing import get_collection

    response = get_collection().get(include=["documents", "metadatas"])
    return [
        {"id": item_id, "content": content, "metadata": dict(metadata)}
        for item_id, content, metadata in zip(
            response["ids"], response["documents"], response["metadatas"]
        )
    ]


def get_corpus() -> list[dict]:
    """Trả về CORPUS, nạp từ ChromaDB ở lần gọi đầu."""
    if not CORPUS:
        CORPUS.extend(load_corpus())
    return CORPUS


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Okapi

    return BM25Okapi([tokenize(item["content"]) for item in corpus])


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if top_k <= 0:
        return []

    corpus = get_corpus()
    tokens = tokenize(query)
    if not corpus or not tokens:
        return []

    bm25 = build_bm25_index(corpus)
    scores = bm25.get_scores(tokens)

    ranked = sorted(range(len(corpus)), key=lambda index: scores[index], reverse=True)
    results = []
    for index in ranked[:top_k]:
        # Chỉ loại score âm. Score 0 vẫn giữ: BM25 cho IDF = 0 khi term xuất
        # hiện ở nửa số document, nên corpus nhỏ có thể toàn score 0 mà vẫn
        # đúng thứ tự. RRF ở Task 7 chỉ dùng rank nên giá trị 0 không ảnh hưởng.
        if scores[index] < 0:
            continue
        item = corpus[index]
        results.append(
            {
                "id": item["id"],
                "content": item["content"],
                "score": float(scores[index]),
                "metadata": dict(item["metadata"]),
                "retrieval_method": "bm25",
            }
        )
    return results


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
