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

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"

EMBED_BATCH_SIZE = 16
# Độ dài tối đa của một dòng được coi là tiêu đề; dài hơn là câu văn thường.
MAX_HEADING_CHARS = 100
# Mẩu vụn từ số trang hoặc dòng kẻ bảng trong PDF, bỏ trước khi đánh chunk_index.
MIN_CHUNK_CHARS = 30
# Chroma từ chối metadata có giá trị None nên url rỗng được lưu thành "".
EMPTY_URL = ""


@lru_cache(maxsize=1)
def _sentence_transformer():
    """Load model một lần cho cả tiến trình."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed danh sách text bằng provider trong .env.

    Task 5 phải gọi đúng hàm này để query và corpus cùng model, cùng dimension.
    """
    if not texts:
        return []

    if EMBEDDING_PROVIDER == "sentence_transformers":
        model = _sentence_transformer()
        vectors = model.encode(
            texts,
            batch_size=EMBED_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > EMBED_BATCH_SIZE,
        )
        return [vector.tolist() for vector in vectors]

    if EMBEDDING_PROVIDER == "openai":
        from openai import OpenAI

        client = OpenAI()
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]

    if EMBEDDING_PROVIDER == "gemini":
        from google import genai

        client = genai.Client()
        response = client.models.embed_content(model=EMBEDDING_MODEL, contents=texts)
        return [list(item.values) for item in response.embeddings]

    raise ValueError(f"EMBEDDING_PROVIDER không hỗ trợ: {EMBEDDING_PROVIDER}")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def parse_header(text: str) -> tuple[dict, str]:
    """Tách header metadata do task 3 sinh ra khỏi phần nội dung."""
    head, separator, body = text.partition("\n---\n\n")
    if not separator:
        return {}, text

    fields: dict[str, str] = {}
    title = re.match(r"#\s*(.+)", head.strip())
    if title:
        fields["title"] = title.group(1).strip()
    for key, value in re.findall(r"\*\*(.+?):\*\*\s*(.+)", head):
        fields[key.strip().lower().replace(" ", "_")] = value.strip()
    return fields, body


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        fields, body = parse_header(path.read_text(encoding="utf-8"))
        url = fields.get("source", "")
        documents.append(
            {
                # ID bám theo đường dẫn nên chạy lại không sinh bản ghi mới.
                "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
                "content": body.strip(),
                "metadata": {
                    "source": path.name,
                    "title": fields.get("title") or path.stem,
                    "doc_type": fields.get("doc_type")
                    or ("legal" if "legal" in path.parts else "news"),
                    "url": None if url in {"", "N/A"} else url,
                },
            }
        )
    return documents


def heading_level(line: str) -> int | None:
    """Trả về cấp tiêu đề của một dòng, None nếu không phải tiêu đề.

    Corpus trộn hai kiểu: Markdown ``###`` từ bài crawl, và đánh số văn bản
    pháp quy (``II. MỤC TIÊU``, ``2. Đến năm 2030``, ``Điều 5.``) từ PDF.
    """
    line = line.strip()
    if not line or len(line) > MAX_HEADING_CHARS:
        return None

    markdown = re.match(r"^(#{1,6})\s+\S", line)
    if markdown:
        return len(markdown.group(1))
    if re.match(r"^(Điều|ĐIỀU)\s+\d+", line):
        return 1
    if re.match(r"^[IVXLCDM]+\s*[.\-)]\s*\S", line):
        return 1
    numbered = re.match(r"^(\d+(?:\.\d+)*)\s*[.)]?\s+(\S.*)$", line)
    if numbered and numbered.group(2)[:1].isupper():
        return 1 + numbered.group(1).count(".")
    if re.match(r"^\*\*[^*]+\*\*$", line):
        return 3
    return None


def split_into_sections(content: str) -> list[tuple[str, str]]:
    """Cắt document tại tiêu đề, trả về (breadcrumb, phần thân).

    Breadcrumb giữ chuỗi tiêu đề cha-con, ví dụ ``II. MỤC TIÊU > 2. Đến năm
    2030``, để mọi chunk trong mục đều mang theo ngữ cảnh của mục đó.
    """
    sections: list[tuple[str, str]] = []
    stack: list[tuple[int, str]] = []
    breadcrumb = ""
    body: list[str] = []

    for line in content.splitlines():
        level = heading_level(line)
        if level is None:
            body.append(line)
            continue

        if body:
            sections.append((breadcrumb, "\n".join(body)))
            body = []
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, re.sub(r"^#{1,6}\s+|\*\*", "", line.strip())))
        breadcrumb = " > ".join(title for _, title in stack)

    if body:
        sections.append((breadcrumb, "\n".join(body)))
    return sections or [("", content)]


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index.

    Cắt theo tiêu đề trước rồi mới cắt theo kích thước, nên một chunk không
    bao giờ nằm vắt qua hai mục khác nhau.
    """
    chunks = []
    for document in documents:
        pieces: list[str] = []
        for breadcrumb, body in split_into_sections(document["content"]):
            prefix = f"[{breadcrumb}]\n" if breadcrumb else ""
            splitter = RecursiveCharacterTextSplitter(
                # Chừa chỗ cho breadcrumb để chunk không vượt CHUNK_SIZE.
                chunk_size=max(MIN_CHUNK_CHARS * 2, CHUNK_SIZE - len(prefix)),
                chunk_overlap=CHUNK_OVERLAP,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            for piece in splitter.split_text(body):
                piece = piece.strip()
                if len(piece) >= MIN_CHUNK_CHARS:
                    pieces.append(prefix + piece)

        for index, text in enumerate(pieces):
            chunks.append(
                {
                    "id": f"{document['id']}::chunk-{index}",
                    "content": text,
                    "metadata": {**document["metadata"], "chunk_index": index},
                }
            )
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        return

    collection = get_collection()
    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[
            {**chunk["metadata"], "url": chunk["metadata"]["url"] or EMPTY_URL}
            for chunk in chunks
        ],
    )


def prune_stale_chunks(chunks: list[dict]) -> int:
    """Xóa chunk cũ không còn trong lần chunk mới.

    Đổi tham số chunking làm số chunk mỗi document thay đổi; upsert chỉ ghi đè
    ID trùng nên ID dư của lần trước sẽ ở lại với nội dung cũ nếu không dọn.
    """
    collection = get_collection()
    current = set(collection.get(include=[])["ids"])
    stale = sorted(current - {chunk["id"] for chunk in chunks})
    if stale:
        collection.delete(ids=stale)
    return len(stale)


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    removed = prune_stale_chunks(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks (đã xóa {removed} chunk cũ)")

    collection = get_collection()
    print(f"Collection '{COLLECTION_NAME}' đang giữ {collection.count()} chunks")
    for document in documents:
        count = sum(1 for chunk in chunks if chunk["id"].startswith(f"{document['id']}::"))
        print(f"  {document['id']}: {count} chunks — {document['metadata']['title'][:50]}")


if __name__ == "__main__":
    run_pipeline()
