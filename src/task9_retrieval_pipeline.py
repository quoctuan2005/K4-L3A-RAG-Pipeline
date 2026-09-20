"""
Task 9 — Retrieval pipeline hoàn chỉnh.

Luồng xử lý:
    1. Chạy semantic_search và lexical_search.
    2. Fuse hai danh sách bằng RRF đúng một lần.
    3. Lấy best cosine score gốc từ dense results.
    4. Nếu score dưới threshold, thử PageIndex fallback.
    5. Nếu fallback lỗi, trả hybrid results thay vì crash.

Không so sánh threshold với RRF score vì hai thang đo khác nhau.
"""

import os

from dotenv import load_dotenv

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


load_dotenv()

# Hiệu chỉnh trên corpus du lịch này bằng 5 query in-domain và 4 query
# out-of-domain: dense top-score in-domain 0.66–0.77, out-of-domain 0.39–0.49.
# 0.57 là điểm giữa khoảng trống đó. Corpus khác phải đo lại.
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD") or 0.57)
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Trả về hybrid hoặc pageindex SearchResult."""
    if top_k <= 0:
        return []

    # Lấy rộng hơn top_k để RRF có đủ ứng viên gộp từ hai phía.
    dense = semantic_search(query, top_k=top_k * 2)
    sparse = lexical_search(query, top_k=top_k * 2)

    # Fuse đúng một lần; nhánh A/B dense-only không đi qua RRF.
    hybrid = rerank_rrf([dense, sparse], top_k=top_k) if use_reranking else dense[:top_k]

    # Quyết định fallback dựa trên cosine score gốc của dense, không phải RRF
    # score: RRF chỉ phản ánh thứ hạng nên không so được với threshold.
    best_dense_score = dense[0]["score"] if dense else 0.0
    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback
        except Exception as error:
            # Provider ngoài lỗi thì vẫn trả hybrid, không để UI crash.
            print(f"PageIndex fallback lỗi: {type(error).__name__}: {error}")
    return hybrid[:top_k]


if __name__ == "__main__":
    for result in retrieve("test query", top_k=3):
        print(result)
