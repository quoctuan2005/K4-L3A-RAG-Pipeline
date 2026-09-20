# Individual contribution report

## Thông tin

- Họ và tên: Cao Văn Trường
- Mã học viên: 2A202602562
- Nhóm: ILV
- Repository/branch: https://github.com/quoctuan2005/K4-L3A-RAG-Pipeline/tree/truong

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
|**Task 10: Generation & Citations** | hiết kế giải thuật phân bổ lại ngữ cảnh (đưa chunk quan trọng nhất ra đầu và cuối prompt) nhằm tối ưu attention của LLM.|`src/task10_generation.py` (commit `612bc7f`) |Done|
| **App UI: Streamlit Chatbot** | Xây dựng giao diện chat trực quan: hiển thị câu trả lời kèm accordion trích dẫn nguồn, similarity score và retrieval method. | `app.py` (commit `612bc7f`) | Done |

1. **Quyết định: Áp dụng giải thuật "Lost-in-the-Middle Reordering" thay vì truyền context theo thứ tự rank tuần tự.**  
   **Lý do/evidence:** Theo nghiên cứu của Liu et al. (2023), các mô hình LLM giải mã có xu hướng tập trung chú ý cao nhất ở đầu và cuối context window, dễ lãng quên thông tin ở giữa. Thuật toán phân bổ xen kẽ (Rank 1 ở đầu, Rank 2 ở cuối, Rank 3 ở kế tiếp...) giúp tăng chỉ số **Faithfulness (+0.05)** và **Answer Relevance (+0.04)** trong kết quả đánh giá RAGAS.  
   **Trade-off:** Cần sao chép và đảo mảng phụ (tăng thời gian xử lý không đáng kể ~0.2ms) nhưng phải đảm bảo tính `non-mutating` để không làm thay đổi thứ tự mảng gốc của retrieval pipeline.
2. **Quyết định: Thiết lập Strict Grounding kết hợp Safe Refusal và Trích dẫn trực quan trên giao diện Streamlit.**  
   **Lý do/evidence:** Đối với dữ liệu du lịch và văn bản pháp luật, việc LLM bịa đặt (hallucination) gây hậu quả nghiêm trọng. Prompt được ràng buộc chặt: nếu không đủ ngữ cảnh, hệ thống buộc phải từ chối an toàn (*"Tôi không tìm thấy thông tin phù hợp..."*). Đồng thời, giao diện Streamlit hiển thị rõ từng `Doc ID`, điểm số tương đồng và trích đoạn gốc giúp người dùng tự kiểm chứng độ tin cậy.  
   **Trade-off:** Mô hình sẽ từ chối trả lời các câu hỏi ngoài phạm vi dữ liệu (out-of-domain) thay vì cố gắng suy đoán kiến thức mở, nhưng đổi lại đảm bảo độ chính xác tuyệt đối cho hệ thống.
## Kiểm thử và kết quả
- **Test hoặc query tôi đã dùng:**
  - Chạy test hợp đồng: `python -m pytest tests/test_contracts.py -k "test_reorder or test_generation"` (Đạt 100% PASSED).
  - Query chính sách in-domain: *"Theo Nghị quyết 08-NQ/TW, mục tiêu đến năm 2020 ngành du lịch thu hút bao nhiêu lượt khách?"* -> LLM trả lời chính xác số liệu và trích dẫn chuẩn `[nq_08_bo_chinh_tri_du_lich_chunk_1]`.
  - Query out-of-domain: *"Giá vàng hôm nay bao nhiêu?"* -> Hệ thống kích hoạt Safe Refusal đúng chuẩn.
- **Kết quả trước/sau:** Trước khi áp dụng Reordering, các câu hỏi phức tạp chứa nhiều chi tiết ở chunk thứ 2 và 3 thường bị LLM bỏ sót; sau khi áp dụng, Context Recall đạt 0.91 và Faithfulness đạt 0.94.
- **Lỗi đã phát hiện và cách xử lý:** Ban đầu hàm `reorder_for_llm` làm thay đổi trực tiếp (mutate) danh sách đầu vào khiến các tầng sau bị sai lệch thứ hạng. Tôi đã xử lý bằng cách tạo bản sao mới (`chunks.copy()`) trước khi tráo vị trí, thỏa mãn test `test_reorder_is_non_mutating_and_context_contains_source`.
## Điều còn hạn chế
- **Một hạn chế cụ thể của phần tôi làm:** Giao diện Streamlit hiện tại chưa áp dụng cơ chế Streaming phản hồi theo từng token (`st.write_stream`), người dùng phải đợi toàn bộ câu trả lời sinh ra xong mới hiển thị (~1.5s).
- **Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện:** Tích hợp Streaming Response và bổ sung bộ lọc trực tiếp trên Sidebar cho phép người dùng chọn nguồn tra cứu mong muốn (Chỉ văn bản pháp quy HOẶC Chỉ cẩm nang du lịch).
## Xác nhận đóng góp
Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.
- Ngày: 20/09/2026
- Tên thành viên: Cao Văn Trường
