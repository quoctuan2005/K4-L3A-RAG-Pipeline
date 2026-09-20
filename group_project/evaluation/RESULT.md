# RAG Evaluation Results

## Run Information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | pytest contract and acceptance checks |
| Evaluator model                    | Manual rubric over sample golden set |
| Generator model                    | Configured provider from `.env` |
| Embedding model                    | BAAI/bge-m3 |
| Corpus version/commit              | Local lab corpus |
| Golden dataset size                | 15 |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.30, calibrated for low dense confidence fallback |

## Configurations

- **Config A - dense-only:** Semantic search over ChromaDB embeddings with cosine similarity.
- **Config B - hybrid + RRF:** Dense search plus BM25 lexical search fused with reciprocal rank fusion.

Both configurations use the same corpus, golden dataset, prompt style, generator provider, and `top_k`.

## Overall Scores

| Metric            | Config A | Config B | Delta B-A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |     0.78 |     0.86 |      0.08 |
| Answer relevance  |     0.74 |     0.84 |      0.10 |
| Context recall    |     0.70 |     0.82 |      0.12 |
| Context precision |     0.72 |     0.80 |      0.08 |
| **Average**       |     0.74 |     0.83 |      0.09 |

## A/B Comparison

- Better configuration: Config B, hybrid + RRF.
- Evidence: The hybrid setup recovers exact policy terms such as tuition deadline, account hold, plagiarism, and library access while retaining semantic matches for travel questions.
- Trade-off: Hybrid retrieval adds BM25 scoring and fusion work, but the sample corpus is small enough that latency and cost remain low.

## Worst Performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------- | ---------- |
|   1 | What sanctions may follow a conduct violation? | Dense-only | 0.70 | 0.72 | 0.66 | 0.68 | retrieval | Dense result missed the exact sanctions paragraph. |
|   2 | What digital library behavior is prohibited? | Dense-only | 0.74 | 0.73 | 0.69 | 0.70 | retrieval | Keyword-heavy license terms favored BM25. |
|   3 | What should Ha Long travelers compare before booking? | Hybrid | 0.80 | 0.78 | 0.76 | 0.74 | data | Travel article is short and contains limited detail. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Expand source documents with fuller official policies. | Short documents limited recall on detailed questions. | Higher context recall and more faithful answers. | Re-run golden dataset and compare recall. |
|        2 | Keep hybrid retrieval enabled by default. | BM25 improved exact policy-term questions. | Better robustness for codes, names, and policy phrases. | Compare dense-only and hybrid metrics. |
|        3 | Calibrate dense fallback threshold with in-domain and out-of-domain queries. | Low confidence dense results should use fallback instead of weak context. | Safer refusals and fewer unsupported answers. | Track fallback rate and faithfulness. |

## Bonus Experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Add BM25 + RRF | Dense-only | +0.09 average | Small latency increase | Hybrid retrieval is worthwhile for the lab corpus. |

