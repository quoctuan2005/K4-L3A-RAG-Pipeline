# Individual contribution report

## Thông tin

- **Họ và tên:** Nguyễn Quốc Tuấn
- **Mã học viên:** 2A202602910
- **Nhóm:** Nhóm K4-L3A (RAG Du Lịch Việt Nam)
- **Repository/branch:** quoctuan2005/K4-L3A-RAG-Pipeline / main
- **Vai trò:** Retrieval (Dense & Hybrid Fusion)

---

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| **Task 4: Chunking & Indexing** | Thiết kế chiến lược chia đoạn văn bản (`RecursiveCharacterTextSplitter`, `CHUNK_SIZE=500`, `CHUNK_OVERLAP=50`), nhúng vector bằng model `all-MiniLM-L6-v2` và index 293 chunks vào ChromaDB collection `rag_documents`. Xử lý chuẩn hóa khoảng trắng từ PDF scan. | `src/task4_chunking_indexing.py` | Done |
| **Task 5: Semantic Search** | Cài đặt hàm `semantic_search(query, top_k)` dùng chung embedding model với Task 4, chuyển đổi khoảng cách cosine distance thành cosine similarity score $[0, 1]$, sắp xếp giảm dần và đảm bảo SearchResult contract. | `src/task5_semantic_search.py` | Done |
| **Task 7: Reranking (RRF)** | Cài đặt thuật toán Reciprocal Rank Fusion `rerank_rrf(ranked_lists, top_k, k=60)` theo công thức $\sum \frac{1}{k + \text{rank}}$, loại bỏ trùng lặp ID và gán nhãn `hybrid`. | `src/task7_reranking.py` | Done |
| **Contract Testing & Verification** | Xây dựng và kiểm thử toàn bộ các bài test hợp đồng cho Task 4, Task 5 và Task 7 đảm bảo tuân thủ `docs/MODULE_CONTRACTS.md`. | `tests/test_contracts.py` | Done |

---

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Chọn tham số `CHUNK_SIZE=500` và `CHUNK_OVERLAP=50` kết hợp chuẩn hóa khoảng trắng thừa (`re.sub(r"[ \t]+", " ", line)`) cho toàn bộ tài liệu Markdown.  
   **Lý do/evidence:** Kích thước 500 ký tự phù hợp với độ dài một điều khoản quy phạm pháp luật (như mốc mục tiêu 2025/2030 trong QĐ 147/QĐ-TTg) hoặc một đoạn giới thiệu trải nghiệm du lịch. Việc tiền xử lý khoảng trắng giúp loại bỏ triệt để lỗi sinh ra từ OCR bóc tách PDF scan, giúp embedding vector bắt đúng ngữ nghĩa từ khóa thay vì bị nhiễu do khoảng trắng kép.  
   **Trade-off:** Chunk kích thước 500 ký tự làm tăng số lượng chunk (293 chunks), đòi hỏi thời gian index ban đầu lâu hơn một chút, nhưng bù lại tăng Context Precision và Recall đáng kể khi truy xuất.

2. **Quyết định:** Sử dụng thuật toán Reciprocal Rank Fusion (RRF với $k=60$) để kết hợp bảng xếp hạng Dense Search và Sparse BM25 thay vì cộng gộp điểm tuyến tính (Linear Combination).  
   **Lý do/evidence:** Dense cosine similarity (thang đo $[0, 1]$) và BM25 score (thang đo $[0, +\infty)$) có phân phối giá trị khác nhau; việc chuẩn hóa điểm số để cộng tuyến tính dễ bị thiên lệch (bias) nếu không có tập dữ liệu validation lớn để tối ưu trọng số $\alpha$. RRF chỉ dựa trên thứ hạng (rank) của từng chunk trong mỗi danh sách, giúp kết hợp ổn định nhất điểm mạnh bắt keyword của BM25 và bắt ngữ nghĩa của Dense search.  
   **Trade-off:** Điểm số RRF chỉ phản ánh thứ tự ưu tiên tương đối, không dùng làm thước đo khoảng cách ngữ nghĩa tuyệt đối để quyết định fallback (ở Task 9 đã giữ nguyên dense score gốc để so sánh threshold).

---

## Kiểm thử và kết quả

- **Test hoặc query tôi đã dùng:**
  - Chạy test suite hợp đồng: `pytest tests/test_contracts.py -v` (15/15 test passed, trong đó các test `test_chunk_documents_*`, `test_embed_texts_*`, `test_index_to_vectorstore_*`, `test_semantic_search_*`, `test_rrf_*` đều đạt 100%).
  - Truy vấn kiểm thử thực tế: `semantic_search("Du lịch Đà Nẵng mùa nào đẹp nhất?", top_k=3)` và `rerank_rrf([dense, sparse], top_k=5)`.
- **Kết quả trước/sau nếu có:**
  - *Trước khi chuẩn hóa khoảng trắng:* Truy vấn văn bản pháp luật có chứa số liệu ("1.700 - 1.800 nghìn tỷ") chỉ đạt similarity score thấp (~0.45) do PDF gốc có khoảng trắng kép giữa các ký tự.
  - *Sau khi chuẩn hóa:* Điểm similarity đạt > 0.72 và chunk chứa điều khoản được xếp hạng top 1 trong kết quả truy xuất.
- **Lỗi đã phát hiện và cách xử lý:**
  - Phát hiện lỗi `libc++abi: recursive_mutex lock failed` trên macOS ARM64 khi Python teardown C++ destructors của thư viện ChromaDB/ONNX Runtime sau khi hoàn thành index. Đã khắc phục bằng cách gọi `os._exit(0)` ở cuối script để kết thúc tiến trình sạch sẽ.

---

## Điều còn hạn chế

- **Một hạn chế cụ thể của phần tôi làm:** Mô hình embedding `all-MiniLM-L6-v2` là mô hình đa ngôn ngữ tổng quát, khả năng biểu diễn ngữ nghĩa với một số từ viết tắt hành chính đặc thù của Việt Nam (như "VPCP-KGVX", "TCDL") còn phụ thuộc nhiều vào sự hỗ trợ của BM25.
- **Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện:** Thử nghiệm tích hợp mô hình embedding chuyên sâu tiếng Việt (như `bkai-foundation-models/vietnamese-bi-encoder` hoặc `bge-m3` chuyển đổi sang định dạng ONNX cục bộ) để nâng cao hơn nữa độ nhạy ngữ nghĩa cho các câu hỏi tiếng Việt phức tạp.

---

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- **Ngày:** 20/09/2026
- **Tên thành viên:** Nguyễn Quốc Tuấn
