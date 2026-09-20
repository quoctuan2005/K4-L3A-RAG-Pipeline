"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    if not query.strip():
        return []

    query_vectors = embed_texts([query])
    if not query_vectors:
        return []
    query_vector = query_vectors[0]

    collection = get_collection()
    response = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    ids = response.get("ids", [[]])[0] if response.get("ids") else []
    documents = response.get("documents", [[]])[0] if response.get("documents") else []
    metadatas = response.get("metadatas", [[]])[0] if response.get("metadatas") else []
    distances = response.get("distances", [[]])[0] if response.get("distances") else []

    seen_ids = set()
    for item_id, content, metadata, distance in zip(ids, documents, metadatas, distances):
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)
        # Cosine distance to similarity: max(0.0, 1.0 - distance)
        score = max(0.0, 1.0 - float(distance))
        results.append({
            "id": item_id,
            "content": content,
            "score": score,
            "metadata": metadata,
            "retrieval_method": "dense",
        })

    # Sort descending by score
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for result in semantic_search("Du lịch Đà Nẵng mùa nào đẹp nhất?", top_k=3):
        print(f"[{result['score']:.4f}] {result['id']} - {result['metadata'].get('title')}")
        print(result['content'][:120] + "...\n")
    import os
    os._exit(0)
