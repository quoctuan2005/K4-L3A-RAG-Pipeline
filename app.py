import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="Hỏi Đáp Du Lịch Việt Nam — RAG Pipeline",
    page_icon="🇻🇳",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("🇻🇳 Du Lịch Việt Nam")
    st.markdown(
        """
        **Hệ thống RAG Pipeline Hỏi Đáp Thông Minh**
        - **Chủ đề:** Cẩm nang du lịch (Đà Nẵng, Phú Quốc, Hội An, Sa Pa, Hạ Long) & Văn bản chính sách (QĐ 147/QĐ-TTg, CV 1560/VPCP-KGVX, NQ 26-NQ/TW).
        - **Cơ chế:** Hybrid Search (BM25 + Dense) kết hợp RRF Reranking và Lost-in-the-middle context reordering.
        """
    )
    st.divider()
    top_k = st.slider("Số lượng ngữ cảnh (top_k)", min_value=3, max_value=10, value=5, step=1)

    st.subheader("💡 Câu hỏi gợi ý")
    sample_queries = [
        "Mục tiêu phát triển du lịch đến năm 2030 theo QĐ 147/QĐ-TTg?",
        "Thời điểm lý tưởng nhất để du lịch Đà Nẵng là khi nào?",
        "Kinh nghiệm di chuyển ra đảo Phú Quốc bằng tàu cao tốc?",
        "Thành phố Hạ Long được chia thành 2 khu vực nào qua cầu Bãi Cháy?",
        "Mùa lúa chín ở Sa Pa vào tháng mấy và mùa đông có gì?",
    ]
    for sq in sample_queries:
        if st.button(sq, key=f"btn_{sq}", use_container_width=True):
            st.session_state.pending_query = sq

    st.divider()
    if st.button("🗑️ Xóa lịch sử trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🏝️ Trợ Lý Du Lịch & Chính Sách Phát Triển Du Lịch Việt Nam")
st.caption("Tra cứu cẩm nang điểm đến và các chiến lược, định hướng phát triển du lịch Việt Nam với trích dẫn minh bạch.")

# Hiển thị lịch sử hội thoại
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            retrieval_method = message.get("retrieval_source", "hybrid").upper()
            with st.expander(f"📚 Nguồn tham khảo & Trích dẫn ({len(message['sources'])} tài liệu | Phương thức: {retrieval_method})"):
                for i, src in enumerate(message["sources"], 1):
                    meta = src.get("metadata", {})
                    score = src.get("score", 0.0)
                    method = src.get("retrieval_method", "hybrid")
                    title = meta.get("title", "Không có tiêu đề")
                    source_file = meta.get("source", "Nguồn tài liệu")
                    url = meta.get("url")

                    header = f"**{i}. {title}** *(Nguồn: `{source_file}` | Độ tương đồng: `{score:.4f}` | Cơ chế: `{method}`)*"
                    if url:
                        header += f" — [Xem link bài viết]({url})"
                    st.markdown(header)
                    st.info(src.get("content", ""))

# Xử lý input từ user hoặc từ nút câu hỏi gợi ý
user_input = st.chat_input("Nhập câu hỏi về du lịch hoặc văn bản chính sách...")
query = user_input or st.session_state.pop("pending_query", None)

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm tài liệu và tổng hợp câu trả lời..."):
            gen_result = generate_with_citation(query, top_k=top_k)
            answer = gen_result.get("answer", "Tôi không thể xác minh thông tin này từ nguồn hiện có.")
            sources = gen_result.get("sources", [])
            retrieval_source = gen_result.get("retrieval_source", "hybrid")

            st.markdown(answer)

            if sources:
                with st.expander(f"📚 Nguồn tham khảo & Trích dẫn ({len(sources)} tài liệu | Phương thức: {retrieval_source.upper()})"):
                    for i, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        score = src.get("score", 0.0)
                        method = src.get("retrieval_method", "hybrid")
                        title = meta.get("title", "Không có tiêu đề")
                        source_file = meta.get("source", "Nguồn tài liệu")
                        url = meta.get("url")

                        header = f"**{i}. {title}** *(Nguồn: `{source_file}` | Độ tương đồng: `{score:.4f}` | Cơ chế: `{method}`)*"
                        if url:
                            header += f" — [Xem link bài viết]({url})"
                        st.markdown(header)
                        st.info(src.get("content", ""))

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source,
    })
