"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""


CORPUS: list[dict] = []


from collections import Counter
import math

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    class BM25Okapi:  # type: ignore
        def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
            self.k1 = k1
            self.b = b
            self.corpus_size = len(corpus)
            self.doc_lengths = [len(doc) for doc in corpus]
            self.avgdl = sum(self.doc_lengths) / max(1, self.corpus_size)
            self.doc_freqs = []
            self.idf = {}
            df = Counter()
            for doc in corpus:
                counts = Counter(doc)
                self.doc_freqs.append(counts)
                for word in counts:
                    df[word] += 1
            for word, freq in df.items():
                self.idf[word] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

        def get_scores(self, query: list[str]) -> list[float]:
            scores = [0.0] * self.corpus_size
            for q in query:
                if q not in self.idf:
                    continue
                idf = self.idf[q]
                for i, doc_freq in enumerate(self.doc_freqs):
                    freq = doc_freq.get(q, 0)
                    if freq > 0:
                        num = freq * (self.k1 + 1)
                        denom = freq + self.k1 * (1 - self.b + self.b * (self.doc_lengths[i] / max(1e-6, self.avgdl)))
                        scores[i] += idf * (num / denom)
            return scores


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    tokenized = [item["content"].lower().split() for item in corpus]
    return BM25Okapi(tokenized)


def _ensure_corpus() -> None:
    """Tự động nạp corpus nếu chưa được khởi tạo."""
    global CORPUS
    if not CORPUS:
        try:
            from .task4_chunking_indexing import chunk_documents, load_documents
            CORPUS = chunk_documents(load_documents())
        except Exception:
            CORPUS = []


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    _ensure_corpus()
    if not CORPUS:
        return []

    bm25 = build_bm25_index(CORPUS)
    scores = bm25.get_scores(query.lower().split())

    # Sort indices by score descending
    sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    results: list[dict] = []

    for index in sorted_indices:
        if scores[index] <= 0 and len(results) > 0:
            continue
        item = CORPUS[index]
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": float(scores[index]),
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })
        if len(results) >= top_k:
            break

    return results


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
