import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot Du lịch Việt Nam",
    page_icon="",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []


def render_sources(sources: list[dict], retrieval_source: str) -> None:
    """Hiển thị đúng các SearchResult đã đưa vào context.

    Không in URL do model sinh ra: mọi thứ ở đây lấy từ metadata của chunk nên
    citation truy ngược được về nguồn gốc.
    """
    if not sources:
        st.info(f"Không có nguồn nào được dùng (retrieval_source = {retrieval_source}).")
        return

    st.caption(f"{len(sources)} nguồn — retrieval_source: **{retrieval_source}**")
    for index, source in enumerate(sources, 1):
        metadata = source["metadata"]
        label = (
            f"[{index}] {metadata['title'][:70]} — "
            f"{source['retrieval_method']} / score {source['score']:.4f}"
        )
        with st.expander(label):
            st.markdown(
                f"**File:** `{metadata['source']}` &nbsp;|&nbsp; "
                f"**Loại:** {metadata['doc_type']} &nbsp;|&nbsp; "
                f"**Chunk:** {metadata['chunk_index']} &nbsp;|&nbsp; "
                f"**Chunk ID:** `{source['id']}`"
            )
            if metadata.get("url"):
                st.markdown(f"**Nguồn công khai:** {metadata['url']}")
            st.markdown("---")
            st.markdown(source["content"])


with st.sidebar:
    st.title("RAG Chatbot")
    st.caption("Hỏi đáp về chính sách và cẩm nang du lịch Việt Nam")
    top_k = st.slider("Số chunks", 3, 10, 5)
    st.markdown(
        "**Corpus:** 4 văn bản chính sách (Công văn 1560/VPCP-KGVX, "
        "Nghị quyết Bộ Chính trị, QĐ 147/QĐ-TTg, TCVN 13259:2020) và "
        "5 cẩm nang du lịch VnExpress (Đà Nẵng, Phú Quốc, Hội An, Sa Pa, Hạ Long)."
    )

st.title("RAG Chatbot Du lịch Việt Nam")
st.caption(
    "Nhập câu hỏi về chính sách du lịch hoặc kinh nghiệm đi các điểm đến trên. "
    "Câu hỏi ngoài phạm vi corpus sẽ nhận câu từ chối thay vì câu trả lời bịa."
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(
                message.get("sources", []),
                message.get("retrieval_source", "none"),
            )

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang truy xuất và tạo câu trả lời..."):
            result = generate_with_citation(query, top_k)

        st.markdown(result["answer"])
        render_sources(result["sources"], result["retrieval_source"])

    # Lưu đủ dữ liệu để render lại nguồn của câu trả lời cũ.
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "retrieval_source": result["retrieval_source"],
        }
    )
