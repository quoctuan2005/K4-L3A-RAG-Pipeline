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
from pathlib import Path
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm:
# CHUNK_SIZE = 500 phù hợp với đoạn văn tiếng Việt đủ ý, CHUNK_OVERLAP = 50 giữ ngữ cảnh tiếp giáp.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIM = 384 if "MiniLM" in EMBEDDING_MODEL else 1024

COLLECTION_NAME = "rag_documents"

_EMBED_MODEL = None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed danh sách văn bản thành list vector floats."""
    if not texts:
        return []

    global _EMBED_MODEL
    provider = os.getenv("EMBEDDING_PROVIDER", EMBEDDING_PROVIDER).lower()

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        resp = client.embeddings.create(input=texts, model=model_name)
        return [item.embedding for item in resp.data]

    if provider == "gemini":
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        embeddings = []
        for text in texts:
            resp = client.models.embed_content(model=model_name, contents=text)
            embeddings.append(resp.embedding.values)
        return embeddings

    # Mặc định local ONNX (all-MiniLM-L6-v2) / sentence_transformers
    if _EMBED_MODEL is None:
        try:
            import chromadb.utils.embedding_functions as ef
            _EMBED_MODEL = ef.DefaultEmbeddingFunction()
        except Exception:
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL)
            _EMBED_MODEL = SentenceTransformer(model_name)

    if hasattr(_EMBED_MODEL, "encode"):
        vectors = _EMBED_MODEL.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return vectors.tolist()
    else:
        return _EMBED_MODEL(texts)


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
        if path.name.startswith("."):
            continue
        doc_type = "legal" if "legal" in path.parts else "news"
        raw_content = path.read_text(encoding="utf-8").strip()
        if not raw_content:
            continue
        cleaned_lines = [re.sub(r"[ \t]+", " ", line) for line in raw_content.splitlines()]
        content = "\n".join(cleaned_lines).strip()

        title = path.stem
        url = None
        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("# ") and title == path.stem:
                title = line_str[2:].strip()
            elif line_str.startswith("**Source:**"):
                cand = line_str.replace("**Source:**", "").strip()
                if cand.startswith("http"):
                    url = cand

        doc_id = path.relative_to(STANDARDIZED_DIR).as_posix()
        documents.append({
            "id": doc_id,
            "content": content,
            "metadata": {
                "source": path.name,
                "title": title,
                "doc_type": doc_type,
                "url": url,
            },
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for document in documents:
        raw_chunks = splitter.split_text(document["content"])
        chunk_idx = 0
        for text in raw_chunks:
            t = text.strip()
            if not t:
                continue
            chunks.append({
                "id": f"{document['id']}::chunk-{chunk_idx}",
                "content": t,
                "metadata": {
                    **document["metadata"],
                    "chunk_index": chunk_idx,
                },
            })
            chunk_idx += 1
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    if not chunks:
        return []
    contents = [chunk["content"] for chunk in chunks]
    vectors = embed_texts(contents)
    embedded_chunks = []
    for chunk, vector in zip(chunks, vectors):
        c = dict(chunk)
        c["embedding"] = vector
        embedded_chunks.append(c)
    return embedded_chunks


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        return
    collection = get_collection()
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.upsert(
            ids=[c["id"] for c in batch],
            documents=[c["content"] for c in batch],
            embeddings=[c["embedding"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    print(f"Loaded {len(documents)} documents.")
    chunks = chunk_documents(documents)
    print(f"Created {len(chunks)} chunks.")
    embedded_chunks = embed_chunks(chunks)
    print(f"Embedded {len(embedded_chunks)} chunks.")
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks into Chroma collection '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    run_pipeline()
    import os
    os._exit(0)
