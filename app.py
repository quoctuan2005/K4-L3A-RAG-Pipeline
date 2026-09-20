import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="Trợ lý Du lịch Việt Nam — RAG Chatbot",
    page_icon="🇻🇳",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("🇻🇳 RAG Du lịch Việt Nam")
    st.caption("Hệ thống Hybrid RAG Pipeline trả lời câu hỏi về chính sách và cẩm nang du lịch Việt Nam.")
    st.markdown("---")
    top_k = st.slider("Số lượng chunks truy xuất (Top K)", min_value=3, max_value=10, value=5)
    
    st.markdown("### 📚 Cơ sở tri thức (Corpus)")
    st.markdown("""
    * **Chính sách & Quy định:**
      * CV 1560/VPCP-KGVX (Mở cửa du lịch)
      * NQ 08-NQ/TW (Du lịch thành ngành kinh tế mũi nhọn)
      * VB 908/TCDL (Giấy phép dịch vụ lữ hành)
    * **Cẩm nang du lịch thực tế:**
      * Cẩm nang Đà Nẵng, Phú Quốc, Hội An, Sa Pa, Hạ Long
    """)
    st.markdown("---")
    if st.button("🗑️ Xóa lịch sử trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🇻🇳 Trợ lý Thông tin Du lịch Việt Nam")
st.caption("Hỏi đáp về quy chế pháp lý, chính sách mở cửa, cùng cẩm nang trải nghiệm, khách sạn, ẩm thực và điểm đến.")

# Hiển thị lịch sử trò chuyện
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("sources"):
            with st.expander(f"📌 Nguồn trích dẫn ({len(message['sources'])} tài liệu | Phương thức: {message.get('retrieval_source', 'hybrid')})"):
                for idx, src in enumerate(message["sources"], 1):
                    meta = src.get("metadata", {})
                    st.markdown(f"**[{idx}] {meta.get('title', 'Tài liệu')}** (File: `{meta.get('source', '')}` | Độ tương đồng: `{src.get('score', 0.0):.4f}`)")
                    st.caption(src.get("content", "")[:350] + ("..." if len(src.get("content", "")) > 350 else ""))

query = st.chat_input("Nhập câu hỏi về du lịch hoặc chính sách (ví dụ: Đà Nẵng mùa nào đẹp nhất?, Mục tiêu phát triển du lịch đến 2030?)...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm tài liệu và tổng hợp câu trả lời có trích dẫn..."):
            result = generate_with_citation(query, top_k=top_k)
            answer = result["answer"]
            sources = result.get("sources", [])
            retrieval_source = result.get("retrieval_source", "hybrid")

            st.markdown(answer)

            if sources:
                with st.expander(f"📌 Nguồn trích dẫn ({len(sources)} tài liệu | Phương thức: {retrieval_source})"):
                    for idx, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        st.markdown(f"**[{idx}] {meta.get('title', 'Tài liệu')}** (File: `{meta.get('source', '')}` | Score: `{src.get('score', 0.0):.4f}`)")
                        st.caption(src.get("content", "")[:350] + ("..." if len(src.get("content", "")) > 350 else ""))

    # Lưu vào session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source,
    })
