"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    query_vectors = embed_texts([query])
    if not query_vectors:
        return []

    collection = get_collection()
    response = collection.query(
        query_embeddings=query_vectors,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    results: list[dict] = []
    ids = response.get("ids", [[]])[0]
    docs = response.get("documents", [[]])[0]
    metas = response.get("metadatas", [[]])[0]
    distances = response.get("distances", [[]])[0]

    for item_id, content, metadata, distance in zip(ids, docs, metas, distances):
        results.append({
            "id": item_id,
            "content": content,
            "score": float(max(0.0, 1.0 - distance)),
            "metadata": metadata,
            "retrieval_method": "dense",
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for result in semantic_search("test query", top_k=3):
        print(result)
