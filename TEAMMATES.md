# DANH SÁCH THÀNH VIÊN NHÓM VÀ PHÂN CÔNG CÔNG VIỆC

**Đề tài:** Hệ thống RAG Pipeline Hỏi Đáp Cẩm Nang Du Lịch & Chính Sách Phát Triển Du Lịch Việt Nam  
**Khóa học:** VinAI - K4 L3A RAG Pipeline  

---

## 1. Thông tin thành viên nhóm

| STT | Họ và tên | Mã học viên | Vai trò chính | Nhánh / Phần việc phụ trách |
| :---: | :--- | :---: | :--- | :--- |
| 1 | **Đào Đức Anh** | `2A202602567` | **Data** | Thu thập văn bản pháp lý, cào dữ liệu VnExpress và chuẩn hóa Markdown (Task 1, 2, 3) |
| 2 | **Nguyễn Quốc Tuấn** | `2A202602910` | **Retrieval** | Chunking, Vector Indexing ChromaDB, Semantic Search và RRF Reranking (Task 4, 5, 7) |
| 3 | **Trần Thu Phương** | `2A202602366` | **Retrieval** | Lexical Search BM25Okapi, tối ưu IDF và Vectorless Fallback PageIndex (Task 6, 8) |
| 4 | **Cao Văn Trường** | `2A202602562` | **Generation & UI** | Generation có trích dẫn, Lost-in-the-middle & Giao diện Streamlit Chatbot (Task 10 & App UI) |
| 5 | **Nguyễn Mạnh Hải** | `2A202602988` | **Evaluation & Integration** | Tích hợp pipeline, Golden Dataset, Ragas A/B Testing & Báo cáo kết quả (Task 9 & Evaluation) |

---

## 2. Chi tiết phân công công việc theo từng module

### 1. Đào Đức Anh — Role: Data
- **Task 1 — Thu thập tài liệu pháp lý:** Tìm kiếm, chọn lọc $\ge 3$ văn bản quy phạm pháp luật du lịch Việt Nam định dạng PDF (`QĐ 147/QĐ-TTg`, `Công văn 1560/VPCP-KGVX`, `Nghị quyết 26-NQ/TW`) lưu tại `data/landing/legal/`.
- **Task 2 — Cào bài viết cẩm nang du lịch:** Viết mã cào dữ liệu tự động từ VnExpress cho 5 điểm đến nổi tiếng (Đà Nẵng, Phú Quốc, Hội An, Sa Pa, Hạ Long), lưu cấu trúc JSON kèm metadata tại `data/landing/news/` (`src/task2_crawl_news.py`).
- **Task 3 — Chuẩn hóa dữ liệu:** Chuyển đổi toàn bộ tài liệu PDF và JSON sang định dạng Markdown chuẩn hóa ($\ge 200$ ký tự mỗi tài liệu) lưu tại `data/standardized/` (`src/task3_convert_markdown.py`).

### 2. Nguyễn Quốc Tuấn — Role: Retrieval (Dense & Hybrid Fusion)
- **Task 4 — Chunking & Indexing:** Thiết kế chiến lược chia đoạn văn bản (`RecursiveCharacterTextSplitter`, `CHUNK_SIZE=500`, `CHUNK_OVERLAP=50`), nhúng vector (`embed_texts`) và lưu trữ vào ChromaDB (`src/task4_chunking_indexing.py`).
- **Task 5 — Semantic Search (Dense):** Cài đặt tìm kiếm ngữ nghĩa qua ChromaDB, chuyển đổi cosine distance thành cosine similarity score $[0, 1]$ (`src/task5_semantic_search.py`).
- **Task 7 — Reciprocal Rank Fusion (RRF):** Cài đặt thuật toán RRF với công thức $RRF(d) = \sum \frac{1}{k + \text{rank}}$ ($k=60$) để kết hợp bảng xếp hạng dense và sparse, khử trùng lặp và gán nhãn `hybrid` (`src/task7_reranking.py`).

### 3. Trần Thu Phương — Role: Retrieval (Sparse & Vectorless Fallback)
- **Task 6 — Lexical Search (BM25):** Triển khai tìm kiếm từ khóa chính xác BM25Okapi, tối ưu hóa IDF xử lý tên địa danh, số hiệu văn bản pháp luật và từ ghép tiếng Việt (`src/task6_lexical_search.py`).
- **Task 8 — Vectorless Fallback Search:** Tích hợp cơ chế fallback dự phòng qua PageIndex, xử lý ngoại lệ an toàn tránh crash pipeline khi dịch vụ ngoài gián đoạn (`src/task8_pageindex_vectorless.py`).
- **Benchmark Retrieval:** So sánh hiệu năng và độ bao phủ giữa Dense Search vs Lexical Search phục vụ cho việc hiệu chỉnh RRF.

### 4. Cao Văn Trường — Role: Generation / UI
- **Task 10 — Generation có Citation:** 
  - Xây dựng hàm `reorder_for_llm` áp dụng kỹ thuật *Lost-in-the-middle* đưa các chunk quan trọng nhất về đầu và cuối ngữ cảnh.
  - Cấu hình Prompt Engineering buộc mô hình trả lời dựa trên context và trích dẫn rõ nguồn [Tài liệu X: Tiêu đề].
  - Tích hợp gọi LLM linh hoạt (Gemini 2.5 Flash, OpenAI GPT-4o-mini, Anthropic Claude) (`src/task10_generation.py`).
- **Streamlit Chat UI (`app.py`):**
  - Thiết kế giao diện trò chuyện trực quan, thân thiện cho chủ đề Du lịch Việt Nam.
  - Tích hợp thanh trượt chọn số lượng chunk (`top_k`), nút câu hỏi gợi ý nhanh và nút xóa lịch sử hội thoại.
  - Trình bày câu trả lời kèm mục mở rộng hiển thị chi tiết nguồn trích dẫn, điểm tương đồng và cơ chế truy xuất (`HYBRID`).
  - Cấu hình `.streamlit/config.toml` tối ưu vận hành không bị lỗi watcher.

### 5. Nguyễn Mạnh Hải — Role: Evaluation & Integration
- **Task 9 — Retrieval Pipeline Integration:** 
  - Kết nối luồng tìm kiếm lai (Hybrid Search: Dense + BM25 $\rightarrow$ RRF Rerank).
  - So sánh điểm cosine score của Dense search với `SCORE_THRESHOLD` (ngưỡng 0.3) để kích hoạt fallback PageIndex hợp lý (`src/task9_retrieval_pipeline.py`).
- **Xây dựng Golden Dataset:** Soạn thảo 16 trường hợp kiểm thử câu hỏi - đáp - ngữ cảnh thực tế (grounded) bao phủ cả văn bản pháp luật và cẩm nang du lịch tại `group_project/evaluation/golden_dataset.json`.
- **Đánh giá định lượng Ragas A/B Testing:**
  - Thiết lập thực nghiệm so sánh A/B giữa **Config A (Dense-only)** và **Config B (Hybrid + RRF)** trên 4 tiêu chí: *Faithfulness*, *Answer Relevance*, *Context Recall*, *Context Precision*.
  - Hoàn thiện báo cáo đánh giá và phân tích Worst Performers tại `group_project/evaluation/RESULT.md`.
- **System Testing:** Điều phối, chạy thử nghiệm toàn bộ hệ thống và đảm bảo vượt qua 20/20 test cases (`tests/test_contracts.py` & `tests/test_acceptance.py`).
