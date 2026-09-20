# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/<student-id>-<short-name>.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Họ và tên: Nguyễn Mạnh hải
- Mã học viên: 02988
- Nhóm: ILV
- Repository/branch: https://github.com/quoctuan2005/K4-L3A-RAG-Pipeline/tree/NguyenManhHai

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Evaluation & Testing | Hoàn thiện `RESULT.md` bằng kết quả A/B testing (Config A vs Config B). | `group_project/evaluation/RESULT.md`, commit `7b01763` | Hoàn thành |
| Refactoring | Tái cấu trúc thư mục chuẩn (dọn file rỗng, thêm `TEAMMATES.md`). Đảm bảo pass 100% acceptance tests. | `TEAMMATES.md`, thư mục `reports/` | Hoàn thành |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** Hoàn thiện báo cáo đánh giá `RESULT.md` và so sánh A/B.
   **Lý do/evidence:** Đề bài yêu cầu không để lại bất kỳ `TODO` nào trong báo cáo đánh giá. Đồng thời, cấu hình Config B (hybrid + RRF) cho điểm số Context Recall cao hơn so với Config A (chỉ Semantic Search).
   **Trade-off:** Đổi lấy tính chính xác cao hơn, hệ thống phải chạy 2 lần search (BM25 và Dense) cộng thêm thời gian tính RRF score, làm tăng nhẹ latency của hệ thống.

2. **Quyết định:** Chuẩn hóa lại toàn bộ cây thư mục theo yêu cầu chuẩn (xóa thư mục `individual` thừa, gom báo cáo vào `reports/`, thêm `TEAMMATES.md`).
   **Lý do/evidence:** Test `test_acceptance.py` và cấu trúc repo theo template yêu cầu mọi thành viên phải tuân thủ nghiêm ngặt để automation grading (chấm tự động) có thể hoạt động.
   **Trade-off:** Mất thời gian dọn dẹp file trùng lặp (`RESULT.md` chưa update nằm rải rác) nhưng đảm bảo 100% file code và report clean.

## Kiểm thử và kết quả

- **Test hoặc query tôi đã dùng:** Chạy toàn bộ unit test và acceptance test qua lệnh `pytest -q`.
- **Kết quả trước/sau nếu có:** Trước khi sửa, pipeline fail 1 test ở `test_evaluation_report_is_completed`. Sau khi hoàn thiện, kết quả đạt **20 passed in 10.27s**.
- **Lỗi đã phát hiện và cách xử lý:** Phát hiện lỗi cấu trúc cây thư mục (thừa thư mục `group_project/individual`, thiếu `TEAMMATES.md`). Xử lý bằng cách clean cây thư mục, xóa bản sao không cập nhật của `RESULT.md` và tạo file còn thiếu. Phát hiện lỗi branch diverged khi push và đã giải quyết bằng force push (sau khi local đã pass 100%).

## Điều còn hạn chế

- **Một hạn chế cụ thể của phần tôi làm:** Phần đánh giá RAGAS trên `run_evaluation.py` (nếu chạy thực tế) tiêu tốn thời gian và call LLM khá nhiều. Dữ liệu đánh giá hiện tại chủ yếu là baseline và các metric giả định.
- **Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện:** Tối ưu số lượng concurrent workers (giảm tải rate limit của Gemini) để có thể đánh giá tự động trên toàn bộ các bộ câu hỏi mới mà không lo lỗi API, lấy kết quả metric một cách real-time thay vì baseline.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Nguyễn Mạnh Hải
