# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | Ragas 0.2.x, ChromaDB 0.6.x, LangChain 0.3.x |
| Evaluator model                    | Gemini 2.5 Flash / GPT-4o-mini |
| Generator model                    | Gemini 2.5 Flash |
| Embedding model                    | all-MiniLM-L6-v2 (Chroma ONNX, 384 dimensions) |
| Corpus version/commit              | Vietnam Tourism corpus (3 legal PDFs, 5 travel articles) |
| Golden dataset size                | 16 grounded cases |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.3 (calibrated on tourism vs out-of-domain queries) |

## Configurations

- **Config A — dense-only:** Semantic search thuần túy sử dụng ChromaDB vector store (`all-MiniLM-L6-v2`), truy xuất top-5 chunks theo cosine similarity mà không kết hợp BM25 hay reranking.
- **Config B — hybrid + RRF:** Hybrid retrieval kết hợp dense search (ChromaDB top-10) và lexical search (BM25Okapi top-10), sau đó chuẩn hóa và hợp nhất bằng thuật toán Reciprocal Rank Fusion (RRF, tham số $k=60$) để chọn ra top-5 chunks tối ưu nhất.

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |    0.840 |    0.940 |    +0.100 |
| Answer relevance  |    0.812 |    0.925 |    +0.113 |
| Context recall    |    0.785 |    0.915 |    +0.130 |
| Context precision |    0.750 |    0.880 |    +0.130 |
| **Average**       |    0.797 |    0.915 |    +0.118 |

## A/B comparison

- **Cấu hình tốt hơn:** Config B (Hybrid Search kết hợp RRF) vượt trội toàn diện so với Config A trên cả 4 chỉ số Ragas (Faithfulness, Answer Relevance, Context Recall, Context Precision).
- **Evidence:** Điểm trung bình của Config B đạt 0.915 so với 0.797 của Config A (+14.8%). Đối với các truy vấn chứa từ khóa đặc thù như số hiệu văn bản quy phạm pháp luật ("147/QĐ-TTg", "1560/VPCP-KGVX", "26-NQ/TW") hay tên địa danh riêng biệt ("Bãi Cháy", "Hòn Gai", "Sơn Trà", "Hà Tiên"), tìm kiếm từ vựng BM25 bắt chính xác tuyệt đối các đoạn văn bản chứa mã và tên riêng, khắc phục hoàn toàn nhược điểm "ngữ nghĩa xấp xỉ" của dense vector embedding.
- **Trade-off về latency/cost:** Config B chỉ tăng thêm khoảng 12ms độ trễ xử lý (tính toán BM25 và RRF score) so với Config A. Chi phí API LLM là tương đương do cùng sử dụng `top_k=5` truyền vào mô hình sinh. Đánh đổi độ trễ 12ms để đổi lại mức tăng 14.8% độ chính xác và giảm thiểu ảo giác (hallucination) là hoàn toàn tối ưu trong môi trường thực tế.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Tầm nhìn phát triển du lịch đến năm 2045 theo Nghị quyết số 26-NQ/TW là gì? | Config A | 0.70 | 0.75 | 0.65 | 0.60 | retrieval | Dense search bị nhiễu giữa mốc năm 2030 và 2045 do khoảng cách vector ngữ nghĩa giữa các con số năm quá gần nhau trong cùng văn bản pháp lý. |
|   2 | Thành phố Hạ Long được phân chia thành hai khu vực nào bởi cầu Bãi Cháy? | Config A | 0.78 | 0.72 | 0.70 | 0.68 | retrieval | Dense vector không chú trọng trọng số của tên riêng 'Bãi Cháy' và 'Hòn Gai', dẫn đến trả về các chunk nói chung về khách sạn và vịnh Hạ Long. |
|   3 | Khi tự lái ô tô từ Hà Nội lên Sa Pa thì đi theo lộ trình đường cao tốc nào? | Config B | 0.88 | 0.85 | 0.82 | 0.80 | generation | Mô hình trả lời đúng lộ trình cao tốc Nội Bài - Lào Cai nhưng tự ý bổ sung thêm nhiều lưu ý thời tiết và xe cộ không được hỏi, làm giảm Answer Relevance. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Bổ sung metadata heading và mốc thời gian vào từng chunk | Các câu hỏi về mốc năm 2025/2030/2045 trong văn bản pháp luật bị nhầm lẫn khi cắt chunk nhỏ | Tăng Context Precision lên trên 0.92 cho văn bản pháp quy | Đánh giá lại recall và precision trên nhóm câu hỏi pháp luật |
|        2 | Tích hợp thư viện tách từ tiếng Việt chuyên dụng (PyVi/Underthesea) cho BM25 | Hiện tại BM25 đang tách từ đơn giản bằng khoảng trắng, chưa tận dụng từ ghép tiếng Việt | Tăng điểm khớp chính xác của tên địa danh và thuật ngữ chuyên ngành du lịch | So sánh điểm BM25 top-k trước và sau khi tách từ |
|        3 | Cải tiến Prompt Engineering để kiểm soát độ dài và tập trung của câu trả lời | Một số câu trả lời của LLM sinh thêm thông tin ngoài lề làm giảm điểm Answer Relevance | Tăng điểm Answer Relevance trung bình lên trên 0.95 | Đo lường độ dài câu trả lời và đánh giá lại Answer Relevance |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Lost-in-the-middle reordering | Giữ nguyên thứ tự rank | +0.035 Faithfulness | +0 ms / +0 USD | Sắp xếp chunks quan trọng nhất về hai đầu ngữ cảnh giúp LLM chú ý tốt hơn, giảm đáng kể hiện tượng bỏ sót thông tin ở giữa context |
| Fallback threshold tuning (0.3 vs 0.5) | Ngưỡng mặc định 0.5 | +0.08 Context Recall trên query lạ | +5 ms khi kích hoạt fallback | Ngưỡng 0.3 phân định hiệu quả hơn giữa query in-domain du lịch và query rác ngoài phạm vi dữ liệu |
