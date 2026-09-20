# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | Ragas 0.4.3 / ChromaDB 0.5.0 / Pytest 9.1 |
| Evaluator model                    | gpt-4o / gemini-2.5-flash |
| Generator model                    | gpt-4o-mini |
| Embedding model                    | BAAI/bge-m3 (Dimension: 1024) |
| Corpus version/commit              | git commit (branch: truong) — 8 standardized docs |
| Golden dataset size                | 16 Q&A pairs |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.35 (Hiệu chỉnh qua kiểm thử 10 queries in-domain và 10 queries out-of-domain) |

## Configurations

- **Config A — dense-only:** Truy xuất ngữ nghĩa thuần túy bằng vector embedding qua ChromaDB (HNSW, metric: cosine similarity). Lấy top 5 chunk có cosine similarity cao nhất.
- **Config B — hybrid + RRF:** Kết hợp song song Dense Search (top 10) và Lexical Search BM25Okapi (top 10), sau đó gộp thứ hạng bằng Reciprocal Rank Fusion (RRF với k=60, rank 1-indexed) để lấy top 5 chunk cuối cùng.

Hai config sử dụng cùng golden dataset (16 câu), cùng generator, evaluator, system prompt và `top_k = 5`; chỉ thay đổi retrieval strategy.

## Overall scores

| Metric            | Config A (Dense-only) | Config B (Hybrid + RRF) | Delta B−A |
| ----------------- | --------------------: | ----------------------: | --------: |
| Faithfulness      |                  0.82 |                    0.94 |     +0.12 |
| Answer relevance  |                  0.85 |                    0.92 |     +0.07 |
| Context recall    |                  0.78 |                    0.91 |     +0.13 |
| Context precision |                  0.76 |                    0.89 |     +0.13 |
| **Average**       |             **0.803** |               **0.915** | **+0.112** |

## A/B comparison

- **Cấu hình tốt hơn:** **Config B (Hybrid + RRF)** vượt trội hoàn toàn so với Config A trên cả 4 tiêu chí cốt lõi, đặc biệt là Context Recall (+13%) và Context Precision (+13%).
- **Evidence:**
  - Đối với các câu hỏi tra cứu văn bản pháp quy có chứa mã hiệu chính xác (như `1560/VPCP-KGVX`, `08-NQ/TW`, `908/TCDL`), Dense search thuần túy thường phân tán điểm tương đồng sang các tài liệu du lịch chung chung, trong khi BM25 định vị chính xác 100% chunk chứa số hiệu văn bản lên vị trí đầu tiên.
  - Khi gộp thứ hạng qua RRF ($k=60$), các đoạn văn được cả hai phương pháp cùng đánh giá cao sẽ được đẩy lên vị trí dẫn đầu, giúp bộ lọc ngữ cảnh cho LLM cô đọng và chính xác hơn hẳn.
- **Trade-off về latency/cost:**
  - BM25 chạy trực tiếp trên bộ nhớ RAM chỉ tốn thêm ~2.1 ms, hoàn toàn không phát sinh chi phí gọi API bên ngoài.
  - Tổng thời gian truy xuất của Config B (~25 - 45 ms) hoàn toàn đáp ứng tiêu chuẩn thời gian thực (*real-time response*).

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------- | ---------- |
|   1 | Trong Công văn 1560/VPCP-KGVX, nhiệm vụ cụ thể về triển khai Nghị quyết 11/NQ-CP là gì? | Config A | 0.70 | 0.75 | 0.60 | 0.65 | retrieval | Dense search bị loãng điểm vector do cụm từ 'Nghị quyết số 11/NQ-CP' bị lấn át bởi các từ khóa chung về phục hồi kinh tế. |
|   2 | Bán đảo Sơn Trà có quy định cấm loại phương tiện nào di chuyển trên các tuyến tham quan chính? | Config A | 0.75 | 0.80 | 0.70 | 0.70 | retrieval | Chunking cắt ngang đoạn liệt kê các tuyến đường cấm xe tay ga, khiến ngữ cảnh bị phân mảnh sang hai chunk kế tiếp. |
|   3 | Số tiền vé tham quan bảo tàng Điêu khắc Chăm tại Đà Nẵng là bao nhiêu và có ưu đãi gì cho sinh viên? | Config B | 0.85 | 0.85 | 0.80 | 0.80 | generation | Mô hình trả lời đúng giá vé 60.000đ nhưng bỏ sót chi tiết giảm giá sinh viên do nằm ở phần cuối của chunk. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Bổ sung Markdown Header Splitting kết hợp Recursive Chunking | Trường hợp #2 cho thấy việc chia cắt cơ học dễ làm mất cấu trúc mục cha-con trong văn bản | Giữ trọn vẹn ngữ cảnh của từng điều khoản và tiểu mục | Đo lường Context Precision trên tập câu hỏi chi tiết |
|        2 | Tích hợp Cross-Encoder Reranker (BGE-Reranker-Large hoặc Jina-Reranker) sau bước RRF | RRF giải quyết tốt bài toán dung hợp thứ hạng nhưng chưa tính điểm tương đồng ngữ nghĩa sâu giữa câu hỏi và đoạn văn | Tăng thêm từ 3 - 5% Faithfulness và Context Precision | So sánh kết quả đánh giá A/B trước và sau khi bổ sung Reranker |
|        3 | Tối ưu hóa Lost-in-the-Middle Context Reordering | Trường hợp #3 cho thấy LLM có xu hướng chú ý nhiều hơn vào thông tin ở 2 đầu context | Giảm thiểu hiện tượng bỏ sót thông tin nằm ở giữa ngữ cảnh | Kiểm tra lại các câu hỏi đa thuộc tính trong golden dataset |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Lost-in-the-Middle Reordering (Đưa chunk quan trọng ra 2 đầu context) | Thứ tự xếp hạng tuần tự gốc | Faithfulness: +0.05, Relevance: +0.04 | Latency: +0.2ms, Cost: 0đ | Reordering giúp LLM trích dẫn chính xác hơn các dữ kiện then chốt mà không phát sinh thêm chi phí. |
