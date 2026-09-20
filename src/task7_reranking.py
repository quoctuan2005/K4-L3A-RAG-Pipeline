"""
Task 7 — Reciprocal Rank Fusion.

RRF gộp nhiều bảng xếp hạng mà không cộng trực tiếp cosine score với BM25
score. Công thức: RRF(d) = sum(1 / (k + rank)), rank bắt đầu 1.từ 

Lưu ý: RRF score chỉ phản ánh thứ hạng, không dùng để quyết định fallback.

-> Dùng Jina hoặc self host hoặc bất cứ công cụ nào bạn quen
"""


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhiều ranked lists và trả hybrid SearchResult."""
    if not ranked_lists:
        return []

    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
            if item_id not in items:
                items[item_id] = item

    ranked_ids = sorted(scores.keys(), key=lambda item_id: scores[item_id], reverse=True)
    results = []
    for item_id in ranked_ids[:top_k]:
        res = dict(items[item_id])
        res["score"] = float(scores[item_id])
        res["retrieval_method"] = "hybrid"
        results.append(res)
    return results


if __name__ == "__main__":
    dummy_dense = [{"id": "c1", "content": "A", "score": 0.9, "metadata": {"source": "s", "title": "t", "doc_type": "legal", "url": None, "chunk_index": 0}, "retrieval_method": "dense"}]
    dummy_bm25 = [{"id": "c1", "content": "A", "score": 3.0, "metadata": {"source": "s", "title": "t", "doc_type": "legal", "url": None, "chunk_index": 0}, "retrieval_method": "bm25"}]
    print(rerank_rrf([dummy_dense, dummy_bm25], top_k=1))
