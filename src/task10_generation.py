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

SYSTEM_PROMPT = """Trả lời chỉ từ context được cung cấp.
Mỗi khẳng định phải có citation. Nếu thiếu evidence, hãy từ chối xác minh."""

SAFE_REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."

# Chỉ điền default cho provider đã kiểm chứng model khả dụng; provider khác
# bắt buộc điền LLM_MODEL trong .env để không gọi nhầm tên model.
DEFAULT_MODELS = {"gemini": "gemini-2.5-flash"}
MAX_OUTPUT_TOKENS = 2048
# gemini-2.5-flash bật thinking mặc định và thinking tiêu tốn chính hạn ngạch
# output: đo được 981/1024 token dành cho thinking, câu trả lời bị cắt với
# finish_reason=MAX_TOKENS. Tác vụ này chỉ trích dẫn từ context nên tắt hẳn.
GEMINI_THINKING_BUDGET = 0


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context."""
    # Trả list mới, không sửa input: pipeline còn cần thứ tự gốc để render nguồn.
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        parts.append(
            f"[Document {index} | Title: {metadata['title']} | "
            f"Source: {metadata['source']}]\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def _model_name() -> str:
    model = LLM_MODEL or DEFAULT_MODELS.get(LLM_PROVIDER, "")
    if not model:
        raise ValueError(f"Chưa cấu hình LLM_MODEL cho provider {LLM_PROVIDER}")
    return model


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    model = _model_name()

    if LLM_PROVIDER == "openai":
        from openai import OpenAI

        response = OpenAI().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return response.choices[0].message.content or ""

    if LLM_PROVIDER == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=GEMINI_THINKING_BUDGET
                ),
            ),
        )
        return response.text or ""

    if LLM_PROVIDER == "anthropic":
        from anthropic import Anthropic

        response = Anthropic().messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return "".join(block.text for block in response.content if block.type == "text")

    raise ValueError(f"LLM_PROVIDER không hỗ trợ: {LLM_PROVIDER}")


def _safe_refusal(reason: str = "") -> dict:
    """Ba field đồng bộ: không có answer thì cũng không khoe nguồn."""
    return {
        "answer": f"{SAFE_REFUSAL} {reason}".strip(),
        "sources": [],
        "retrieval_source": "none",
    }


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return _safe_refusal()

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = f"Context:\n{context}\n\nQuestion: {query}"

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception as error:
        # Provider lỗi thì từ chối an toàn, không bịa câu trả lời.
        return _safe_refusal(f"(Lỗi provider: {type(error).__name__})")
    if not answer.strip():
        return _safe_refusal()

    # retrieval_source mô tả đường đã tạo ra sources. Nhánh A/B dense-only
    # (use_reranking=False) vẫn là đường vector nên gộp vào "hybrid";
    # contract chỉ cho phép hybrid | pageindex | none.
    method = chunks[0]["retrieval_method"]
    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": "pageindex" if method == "pageindex" else "hybrid",
    }


if __name__ == "__main__":
    print(generate_with_citation("test query"))
