"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT = """Bạn là trợ lý AI chuyên gia về Du lịch và Chính sách phát triển Du lịch Việt Nam.
Hãy trả lời câu hỏi của người dùng một cách chính xác, rõ ràng và đầy đủ dựa trên các tài liệu trong ngữ cảnh được cung cấp.
Khi nêu các thông tin, địa điểm hoặc số liệu, hãy kèm theo trích dẫn nguồn (ví dụ: [Tài liệu X: Tiêu đề]).
Nếu trong ngữ cảnh hoàn toàn không có thông tin để trả lời câu hỏi, hãy từ chối: 'Tôi không thể xác minh thông tin này từ nguồn hiện có.'"""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context (Lost-in-the-middle)."""
    if not chunks:
        return []
    chunks_copy = list(chunks)
    if len(chunks_copy) <= 2:
        return chunks_copy
    front = chunks_copy[::2]
    back = chunks_copy[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        title = metadata.get("title", "Không có tiêu đề")
        source = metadata.get("source", "Không rõ nguồn")
        content = chunk.get("content", "")
        parts.append(
            f"[Tài liệu {index} | Tiêu đề: {title} | Nguồn: {source}]\n{content}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    provider = (os.getenv("LLM_PROVIDER") or LLM_PROVIDER or "gemini").lower().strip()
    model_name = os.getenv("LLM_MODEL") or LLM_MODEL

    if provider == "gemini":
        from google import genai
        from google.genai import types
        api_key = os.getenv("GEMINI_API_KEY", "")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name or "gemini-2.5-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
            ),
        )
        return response.text or ""

    if provider == "anthropic":
        from anthropic import Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_name or "claude-3-5-haiku-latest",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=TEMPERATURE,
        )
        return response.content[0].text or ""

    # Default: OpenAI
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY", "")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name or "gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=TEMPERATURE,
    )
    return response.choices[0].message.content or ""


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    if not query.strip():
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
        }

    try:
        chunks = retrieve(query, top_k=top_k)
    except Exception:
        chunks = []

    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
        }

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = (
        f"Ngữ cảnh tham khảo:\n{context}\n\n"
        f"Câu hỏi: {query}\n\n"
        "Hãy trả lời câu hỏi dựa trên các tài liệu trên và trích dẫn rõ nguồn/tiêu đề tài liệu."
    )

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
        if not answer or not answer.strip():
            answer = "Tôi không thể xác minh thông tin này từ nguồn hiện có."
    except Exception as e:
        print(f"Lỗi gọi LLM: {e}")
        answer = "Tôi không thể xác minh thông tin này từ nguồn hiện có."

    method = chunks[0].get("retrieval_method", "hybrid")
    retrieval_source = "pageindex" if method == "pageindex" else "hybrid"

    return {
        "answer": answer.strip(),
        "sources": chunks,
        "retrieval_source": retrieval_source,
    }


if __name__ == "__main__":
    result = generate_with_citation("Thời điểm thích hợp du lịch Đà Nẵng là khi nào?")
    print("Answer:\n", result["answer"])
    print("\nRetrieval source:", result["retrieval_source"])
    print(f"\nSources count: {len(result['sources'])}")
    import os as _os
    _os._exit(0)
