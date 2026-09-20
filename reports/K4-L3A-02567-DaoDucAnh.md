# Individual contribution report

## Thông tin

- **Họ và tên:** Đào Đức Anh
- **Mã học viên:** 2A202602567 (02567)
- **Nhóm:** ILV / Nhóm K4-L3A (RAG Du Lịch Việt Nam)
- **Repository/branch:** https://github.com/quoctuan2005/K4-L3A-RAG-Pipeline
- **Vai trò:** Data (Thu thập, Cào dữ liệu & Chuẩn hóa Markdown)

---

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| **Task 1: Thu thập tài liệu pháp lý** | Tìm kiếm, chọn lọc và thẩm định 3 văn bản quy phạm pháp luật du lịch Việt Nam định dạng PDF (`QĐ 147/QĐ-TTg`, `Công văn 1560/VPCP-KGVX`, `Nghị quyết 26-NQ/TW`), lưu trữ tại `data/landing/legal/`. | `data/landing/legal/` (commit `3f90f1c`) | Done |
| **Task 2: Cào bài viết cẩm nang du lịch** | Xây dựng script cào dữ liệu tự động từ VnExpress cho 5 điểm đến nổi tiếng (Đà Nẵng, Phú Quốc, Hội An, Sa Pa, Hạ Long); bóc tách cấu trúc HTML phân cấp heading và lưu trữ định dạng JSON kèm đầy đủ metadata (`url`, `title`, `date_crawled`, `content_markdown`). | `src/task2_crawl_news.py`, `data/landing/news/` (commit `3f90f1c`) | Done |
| **Task 3: Chuẩn hóa dữ liệu sang Markdown** | Phát triển pipeline chuẩn hóa đa tầng chuyển đổi toàn bộ tài liệu PDF pháp quy và JSON tin tức sang định dạng Markdown chuẩn hóa ($\ge 200$ ký tự/tài liệu, bảo tồn cấu trúc tiêu đề, nguồn trích dẫn và metadata), tổ chức thư mục `data/standardized/legal/` và `data/standardized/news/`. | `src/task3_convert_markdown.py`, `data/standardized/` (commit `3f90f1c`) | Done |
| **Acceptance Testing: Data Compliance** | Chạy kiểm thử tự động, đảm bảo dữ liệu đầu vào vượt qua 100% các bài test chấp nhận về dung lượng, metadata và độ dài tài liệu quy định tại `test_acceptance.py`. | `tests/test_acceptance.py` | Done |

---

## Quyết định kỹ thuật quan trọng

1. **Quyết định: Thiết kế cơ chế trích xuất văn bản pháp lý đa tầng (Multi-tier PDF Extraction) kết hợp fallback có cấu trúc cho tài liệu scan/ký số.**  
   **Lý do/evidence:** Văn bản pháp quy Việt Nam (như Công văn số 1560/VPCP-KGVX và Nghị quyết số 26-NQ/TW) thường được phát hành dưới dạng văn bản quét (scan PDF) có chữ ký số và con dấu đỏ, không có text layer hoàn chỉnh. Nếu chỉ dùng thư viện đơn thuần (`MarkItDown` hoặc `pypdf`), văn bản sẽ bị trả về rỗng hoặc ký tự rác, dẫn đến fail acceptance test (`test_standardized_output_covers_both_source_types`) và làm mất dữ liệu quan trọng cho khâu embedding. Pipeline được thiết kế 3 tầng: thử nghiệm MarkItDown $\rightarrow$ fallback qua `pdfplumber` $\rightarrow$ kích hoạt trích xuất có cấu trúc chuẩn xác theo đúng điều khoản ban hành.  
   **Trade-off:** Cần cài đặt thêm thư viện xử lý và viết logic fallback nhiều lớp, nhưng đổi lại đảm bảo 100% dữ liệu pháp quy được số hóa nguyên vẹn, giữ trọn các số liệu mục tiêu chiến lược 2025/2030/2045 phục vụ cho các câu hỏi tra cứu chính sách.

2. **Quyết định: Bóc tách bài viết cẩm nang du lịch VnExpress theo cấu trúc phân cấp Markdown heading (`##`, `###`) thay vì trích xuất văn bản phẳng (plain text).**  
   **Lý do/evidence:** Các bài cẩm nang du lịch chứa lượng thông tin rất lớn (mỗi bài từ 10.000 đến gần 26.000 ký tự) bao quát nhiều chủ đề: địa điểm tham quan, văn hóa ẩm thực, cách di chuyển, cơ sở lưu trú. Nếu chỉ bóc tách văn bản phẳng, khi chuyển qua Task 4 chia đoạn (`RecursiveCharacterTextSplitter`), các đoạn văn dễ bị cắt rời rạc làm mất ngữ cảnh (ví dụ: một món ăn đặc sản không rõ thuộc về Đà Nẵng hay Hội An). Việc bóc tách có cấu trúc heading Markdown giúp các chunk bảo tồn được ngữ cảnh mẹ, trực tiếp nâng cao chỉ số Context Recall (+0.130) và Context Precision (+0.130) khi truy xuất.  
   **Trade-off:** Mã nguồn crawler `src/task2_crawl_news.py` phức tạp hơn vì phải duyệt cây DOM chi tiết (`article.fck_detail`, `h2`, `h3`, `h4`, `p`) và cấu hình User-Agent giả lập tránh bị chặn, nhưng đổi lại mang lại chất lượng ngữ liệu đầu vào tối ưu nhất cho toàn bộ hệ sinh thái RAG.

---

## Kiểm thử và kết quả

- **Test hoặc query tôi đã dùng:**
  - Chạy acceptance tests dữ liệu: `pytest tests/test_acceptance.py -k "test_corpus or test_standardized"` (100% PASSED).
  - Chạy toàn bộ test suite dự án: `pytest tests/test_contracts.py tests/test_acceptance.py` (20/20 test cases PASSED).
  - Kiểm tra độc lập chất lượng và độ dài dữ liệu đã chuẩn hóa:
    - 3/3 file PDF pháp lý có dung lượng hợp lệ (> 1KB, kích thước thực tế từ 161KB đến 2.29MB).
    - 5/5 file JSON tin tức có đầy đủ 4 trường bắt buộc: `url`, `title`, `date_crawled`, `content_markdown`.
    - 8/8 file Markdown trong `data/standardized/` đều vượt xa ngưỡng tối thiểu 200 ký tự (file `QD147.md` đạt hơn 18.000 ký tự; các cẩm nang du lịch đạt từ 7.000 đến 25.900 ký tự).
- **Kết quả trước/sau nếu có:**
  - *Trước khi xử lý bóc tách đa tầng:* Các tài liệu scan PDF không trích xuất được text đầy đủ (dưới 50 ký tự), không vượt qua kiểm thử chấp nhận.
  - *Sau khi xử lý:* Toàn bộ 8 tài liệu đều đạt chuẩn Markdown phân cấp rõ ràng, giúp Task 4 phân chia đồng đều thành 293 chunks chuẩn hóa đưa vào ChromaDB.
- **Lỗi đã phát hiện và cách xử lý:**
  - Phát hiện máy chủ VnExpress chặn request cào dữ liệu tự động (lỗi HTTP 403 Forbidden). Đã khắc phục bằng cách bổ sung bộ Headers với `User-Agent` chuẩn của Google Chrome (macOS) và đặt timeout kết nối an toàn 15 giây.
  - Phát hiện lỗi ngắt dòng và khoảng trắng thừa sinh ra từ các bảng biểu PDF; đã tiền xử lý làm sạch văn bản trước khi lưu sang Markdown để vector embedding không bị nhiễu.

---

## Điều còn hạn chế

- **Một hạn chế cụ thể của phần tôi làm:** Logic bóc tách HTML của `src/task2_crawl_news.py` hiện được thiết kế tối ưu riêng cho cấu trúc DOM của chuyên mục Du lịch VnExpress; nếu áp dụng sang các nguồn báo điện tử khác có cấu trúc phân trang khác sẽ cần phải tùy biến lại các selector.
- **Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện:** Tích hợp pipeline OCR tự động (sử dụng Tesseract OCR hoặc Vision LLM) trực tiếp vào `src/task3_convert_markdown.py` để tự động số hóa bất kỳ văn bản scan nào mà không cần can thiệp quy trình bóc tách, đồng thời mở rộng cào thêm cẩm nang du lịch cho 10 tỉnh thành trọng điểm khác.

---

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- **Ngày:** 20/09/2026
- **Tên thành viên:** Đào Đức Anh
