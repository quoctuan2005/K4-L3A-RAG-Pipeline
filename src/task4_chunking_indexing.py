"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import os
import re
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
STANDARDIZED_DIR = PROJECT_ROOT / "data" / "standardized"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3") or "BAAI/bge-m3"
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"


def _env_value(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


@lru_cache(maxsize=2)
def _get_sentence_transformer(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _markdown_title(content: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
    if not match:
        return fallback
    return match.group(1).strip() or fallback


def _markdown_source_url(content: str) -> str | None:
    match = re.search(r"^\*\*Source:\*\*\s*(.+?)\s*$", content, flags=re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip() or None


def _metadata_for_chroma(metadata: dict) -> dict:
    return {key: ("" if value is None else value) for key, value in metadata.items()}


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    provider = _env_value("EMBEDDING_PROVIDER", EMBEDDING_PROVIDER).lower()
    model_name = _env_value("EMBEDDING_MODEL", EMBEDDING_MODEL)

    if provider in {"sentence_transformers", "sentence-transformers", "local"}:
        model = _get_sentence_transformer(model_name)
        vectors = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return vectors.tolist()

    if provider == "openai":
        from openai import OpenAI

        if not model_name or model_name.startswith("BAAI/"):
            model_name = "text-embedding-3-small"
        response = OpenAI().embeddings.create(model=model_name, input=texts)
        return [item.embedding for item in response.data]

    if provider == "gemini":
        from google import genai

        if not model_name or model_name.startswith("BAAI/"):
            model_name = "gemini-embedding-001"
        response = genai.Client().models.embed_content(
            model=model_name,
            contents=texts,
        )
        return [embedding.values for embedding in response.embeddings]

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider}")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        relative_path = path.relative_to(STANDARDIZED_DIR)
        top_level = relative_path.parts[0] if relative_path.parts else ""
        doc_type = "legal" if top_level == "legal" else "news"
        fallback_title = path.stem.replace("_", " ").replace("-", " ").strip() or path.stem
        documents.append(
            {
                "id": relative_path.as_posix(),
                "content": content,
                "metadata": {
                    "source": relative_path.as_posix(),
                    "title": _markdown_title(content, fallback_title),
                    "doc_type": doc_type,
                    "url": _markdown_source_url(content) if doc_type == "news" else None,
                },
            }
        )
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for document in documents:
        for index, text in enumerate(splitter.split_text(document["content"])):
            content = text.strip()
            if not content:
                continue

            chunks.append(
                {
                    "id": f"{document['id']}::chunk-{index}",
                    "content": content,
                    "metadata": {**document["metadata"], "chunk_index": index},
                }
            )
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    if not chunks:
        return []

    vectors = []
    batch_size = 32
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        vectors.extend(embed_texts([chunk["content"] for chunk in batch]))

    if len(vectors) != len(chunks):
        raise ValueError("Embedding count does not match chunk count")

    return [
        {**chunk, "embedding": vector}
        for chunk, vector in zip(chunks, vectors)
    ]


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        return

    collection = get_collection()
    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[_metadata_for_chroma(chunk["metadata"]) for chunk in chunks],
    )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
