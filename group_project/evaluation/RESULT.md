# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | RAGAS 0.4.3 |
| Evaluator model                    | gemini-2.5-flash |
| Generator model                    | gemini-2.5-flash |
| Embedding model                    | BAAI/bge-m3 |
| Corpus version/commit              | v1.0 |
| Golden dataset size                | 16 |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.57 (calibrated in-domain vs out-of-domain) |

## Configurations

- **Config A — dense-only:** Retrieval bằng semantic search (cosine similarity).
- **Config B — hybrid + RRF:** Kết hợp dense và BM25 bằng Reciprocal Rank Fusion.

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |     0.82 |     0.89 |     +0.07 |
| Answer relevance  |     0.78 |     0.86 |     +0.08 |
| Context recall    |     0.85 |     0.92 |     +0.07 |
| Context precision |     0.80 |     0.85 |     +0.05 |
| **Average**       |     0.81 |     0.88 |     +0.07 |

## A/B comparison

- Cấu hình tốt hơn: Config B (hybrid + RRF)
- Evidence: Trung bình 4 metrics tăng từ 0.81 lên 0.88.
- Trade-off về latency/cost: Config B tốn thêm thời gian query BM25 và tính RRF (khoảng +50ms), nhưng tăng đáng kể accuracy.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Câu hỏi về số liệu du lịch 2030 | Config A |         0.50 |      0.60 |   0.40 |      0.55 | retrieval                 | Thiếu keywords chính xác |
|   2 | Điều kiện an toàn COVID | Config B |         0.65 |      0.70 |   0.60 |      0.65 | generation                | LLM miss detail |
|   3 | Đóng góp GDP 2025 | Config A |         0.55 |      0.65 |   0.50 |      0.60 | data                      | Bảng biểu bị parse lỗi |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Áp dụng Hybrid Search | Điểm Config A thấp ở keyword search | Cải thiện Context Recall | Đánh giá A/B với tập dữ liệu |
|        2 | Nâng cấp parsing | Câu hỏi về GDP trả về sai sót | Nâng Context Precision | Chạy RAGAS pipeline mới |
|        3 | Dùng LLM xịn hơn | Lỗi generation | Tăng Faithfulness | Đổi model LLM |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Thay đổi chunk size từ 500 thành 1000 | Config B |         -0.02 |               +10% | Không hiệu quả |
