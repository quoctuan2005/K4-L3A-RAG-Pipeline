# Individual Contribution Report

## Thông Tin

- Họ và tên: Trần Thu Phương
- Mã học viên: 2A202602366
- Nhóm: ILV
- Repository/branch: https://github.com/quoctuan2005/K4-L3A-RAG-Pipeline
- Role: Retrieval (Sparse & Vectorless Fallback)

## Phần Việc Đã Thực Hiện

### 3. Trần Thu Phương — Role: Retrieval (Sparse & Vectorless Fallback)

- **Task 6 — Lexical Search (BM25):** Triển khai tìm kiếm từ khóa chính xác BM25Okapi, tối ưu hóa IDF xử lý tên địa danh, số hiệu văn bản pháp luật và từ ghép tiếng Việt (`src/task6_lexical_search.py`).
- **Task 8 — Vectorless Fallback Search:** Tích hợp cơ chế fallback dự phòng qua PageIndex, xử lý ngoại lệ an toàn tránh crash pipeline khi dịch vụ ngoài gián đoạn (`src/task8_pageindex_vectorless.py`).
- **Benchmark Retrieval:** So sánh hiệu năng và độ bao phủ giữa Dense Search vs Lexical Search phục vụ cho việc hiệu chỉnh RRF.

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 6 - Lexical Search | Xây dựng BM25 lexical retrieval, tokenize nội dung và query, trả kết quả đúng SearchResult contract | `src/task6_lexical_search.py` | Done |
| Task 8 - Vectorless Fallback | Tạo fallback search an toàn, cache document mapping, trả kết quả `pageindex` khi dense retrieval confidence thấp | `src/task8_pageindex_vectorless.py` | Done |
| Benchmark Retrieval | Đối chiếu dense search và lexical search để hỗ trợ cấu hình hybrid + RRF | `group_project/evaluation/RESULT.md` | Done |

## Quyết Định Kỹ Thuật Quan Trọng

1. **Quyết định:** Bổ sung BM25 song song với dense retrieval.  
   **Lý do/evidence:** Dense search phù hợp truy vấn ngữ nghĩa, nhưng BM25 tốt hơn với từ khóa chính xác như tên địa danh, mã/số hiệu văn bản, thuật ngữ policy và cụm từ tiếng Việt.  
   **Trade-off:** Tăng thêm một bước truy vấn và cần fusion kết quả, nhưng cải thiện recall cho các câu hỏi có keyword rõ ràng.

2. **Quyết định:** Thiết kế fallback vectorless không làm crash pipeline khi dịch vụ ngoài bị lỗi.  
   **Lý do/evidence:** PageIndex là dịch vụ ngoài nên có thể thiếu API key, timeout hoặc gián đoạn. Retrieval pipeline cần tiếp tục trả hybrid results hoặc safe fallback thay vì dừng chương trình.  
   **Trade-off:** Kết quả fallback có thể kém giàu ngữ nghĩa hơn dense retrieval, nhưng tăng độ ổn định khi demo và khi chạy test.

## Kiểm Thử Và Kết Quả

- Test hoặc query tôi đã dùng:
  - `pytest tests/test_contracts.py`
  - `pytest`
  - Query kiểm tra keyword như `tuition fee`, `library opening hours`, `Da Nang`, `Ha Long`.
- Kết quả:
  - Contract tests pass với SearchResult đúng schema, đúng `retrieval_method`.
  - Full test suite pass: `20 passed`.
- Lỗi đã phát hiện và cách xử lý:
  - BM25 có thể trả score 0 với corpus nhỏ; đã điều chỉnh để vẫn trả top-k kết quả tốt nhất thay vì list rỗng.
  - Fallback provider có thể lỗi; đã xử lý ngoại lệ để retrieval pipeline không crash.

## Điều Còn Hạn Chế

- Một hạn chế cụ thể của phần tôi làm: fallback hiện ưu tiên độ ổn định và contract của pipeline, chưa phải tích hợp PageIndex production đầy đủ với API thật.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: benchmark nhiều bộ query tiếng Việt hơn để hiệu chỉnh tokenizer, BM25 score, fallback threshold và trọng số RRF.

## Xác Nhận Đóng Góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Trần Thu Phương

