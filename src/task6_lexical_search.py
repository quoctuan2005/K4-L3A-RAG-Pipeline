"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""


from rank_bm25 import BM25Okapi


CORPUS: list[dict] = []
_CACHED_CORPUS_ID = None
_CACHED_BM25 = None


def get_corpus() -> list[dict]:
    """Lấy hoặc load corpus chunks từ Task 4."""
    global CORPUS
    if not CORPUS:
        from .task4_chunking_indexing import chunk_documents, load_documents
        CORPUS = chunk_documents(load_documents())
    return CORPUS


def build_bm25_index(corpus: list[dict]) -> BM25Okapi:
    """Tạo BM25 index từ corpus chunks."""
    if not corpus:
        return None
    tokenized = [item["content"].lower().split() for item in corpus]
    bm25 = BM25Okapi(tokenized)
    # Đảm bảo các từ trong corpus nhỏ không bị idf <= 0
    for word, val in bm25.idf.items():
        if val <= 0:
            bm25.idf[word] = 0.5
    return bm25


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    global _CACHED_CORPUS_ID, _CACHED_BM25
    if not query.strip():
        return []

    corpus = CORPUS if CORPUS else get_corpus()
    if not corpus:
        return []

    corpus_id = id(corpus)
    if corpus_id != _CACHED_CORPUS_ID or _CACHED_BM25 is None:
        _CACHED_BM25 = build_bm25_index(corpus)
        _CACHED_CORPUS_ID = corpus_id

    bm25 = _CACHED_BM25
    if bm25 is None:
        return []

    query_tokens = query.lower().split()
    scores = bm25.get_scores(query_tokens)

    ranked_indices = sorted(range(len(corpus)), key=lambda i: scores[i], reverse=True)
    results = []
    for idx in ranked_indices:
        score = float(scores[idx])
        if score <= 0:
            continue
        item = corpus[idx]
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": score,
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })
        if len(results) >= top_k:
            break
    return results


if __name__ == "__main__":
    for result in lexical_search("Đà Nẵng Bà Nà Hills", top_k=3):
        print(f"[{result['score']:.4f}] {result['id']} - {result['metadata'].get('title')}")
        print(result['content'][:120] + "...\n")
