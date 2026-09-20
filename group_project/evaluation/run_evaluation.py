"""
Evaluation — Config A (dense-only) vs Config B (hybrid + RRF).

Chạy golden_dataset.json qua hai cấu hình retrieval, giữ nguyên generator,
evaluator, prompt và top_k; đo 4 metric bằng RAGAS: faithfulness, answer
relevancy, context recall, context precision.

Chia hai giai đoạn để không phải chạy lại phần tốn tiền khi giai đoạn sau lỗi:
    1. collect — gọi retrieval + generation thật, lưu group_project/evaluation/runs.json.
    2. score   — chạy RAGAS trên runs.json đã lưu, ghi group_project/evaluation/scores.json.

Dùng:
    python -m group_project.evaluation.run_evaluation collect
    python -m group_project.evaluation.run_evaluation score
    python -m group_project.evaluation.run_evaluation all
"""

import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Console Windows mặc định cp1252, không encode được tiếng Việt khi in
# unbuffered; ép UTF-8 để tránh UnicodeEncodeError giữa chừng chạy.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
load_dotenv()

from src.task9_retrieval_pipeline import retrieve  # noqa: E402
from src.task10_generation import (  # noqa: E402
    SYSTEM_PROMPT,
    call_llm,
    format_context,
    reorder_for_llm,
)

EVAL_DIR = Path(__file__).parent
GOLDEN_PATH = EVAL_DIR / "golden_dataset.json"
RUNS_PATH = EVAL_DIR / "runs.json"
SCORES_PATH = EVAL_DIR / "scores.json"

TOP_K = 5
SAFE_REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."

CONFIGS = {
    "A_dense_only": False,
    "B_hybrid_rrf": True,
}


def run_one(query: str, top_k: int, use_reranking: bool) -> dict:
    """Sinh câu trả lời cho một cấu hình retrieval, đo latency.

    Không gọi generate_with_citation() trực tiếp vì hàm đó khoá cứng
    use_reranking=True (đúng theo contract công khai) — ở đây tái dùng cùng
    các khối reorder_for_llm/format_context/call_llm để Config A đi qua
    đúng logic generation như Config B, chỉ khác nhánh retrieval.
    """
    t0 = time.time()
    chunks = retrieve(query, top_k=top_k, use_reranking=use_reranking)
    retrieval_s = time.time() - t0

    if not chunks:
        return {
            "answer": SAFE_REFUSAL,
            "retrieved_contexts": [],
            "sources": [],
            "retrieval_seconds": retrieval_s,
            "generation_seconds": 0.0,
        }

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = f"Context:\n{context}\n\nQuestion: {query}"

    t1 = time.time()
    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception as error:
        answer = f"{SAFE_REFUSAL} (Lỗi provider: {type(error).__name__})"
    generation_s = time.time() - t1

    return {
        "answer": answer or SAFE_REFUSAL,
        "retrieved_contexts": [chunk["content"] for chunk in chunks],
        "sources": [
            {
                "id": chunk["id"],
                "retrieval_method": chunk["retrieval_method"],
                "score": chunk["score"],
                "source": chunk["metadata"]["source"],
            }
            for chunk in chunks
        ],
        "retrieval_seconds": retrieval_s,
        "generation_seconds": generation_s,
    }


def collect() -> None:
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    runs = []
    for index, case in enumerate(golden, 1):
        row = {
            "case_index": index,
            "question": case["question"],
            "expected_answer": case["expected_answer"],
            "expected_context": case["expected_context"],
        }
        for config_name, use_reranking in CONFIGS.items():
            print(f"[{index}/{len(golden)}] {config_name}: {case['question'][:60]}", flush=True)
            row[config_name] = run_one(case["question"], TOP_K, use_reranking)
        runs.append(row)
        RUNS_PATH.write_text(json.dumps(runs, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nSaved {len(runs)} case runs -> {RUNS_PATH}")


def score() -> None:
    import os

    from openai import OpenAI
    from ragas import EvaluationDataset, SingleTurnSample, evaluate
    from ragas.embeddings.base import BaseRagasEmbeddings
    from ragas.llms import llm_factory
    from ragas.metrics import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness
    from ragas.run_config import RunConfig

    from src.task4_chunking_indexing import embed_texts

    key = os.environ["GEMINI_API_KEY"]
    # Gemini có endpoint tương thích OpenAI; RAGAS 0.4.3 chưa có adapter Gemini
    # native ổn định cho evaluate() (thiếu jsonref cho nhánh instructor), nên
    # dùng client openai đã có sẵn trong pyproject trỏ vào endpoint đó.
    oai_client = OpenAI(
        api_key=key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    # max_tokens thấp làm JSON structured-output của RAGAS (statement
    # decomposition cho faithfulness) bị cắt giữa chừng -> instructor retry
    # nhiều lần, một job từng mất 250s vì việc này. Nâng lên tránh lặp retry.
    eval_llm = llm_factory(
        "gemini-2.5-flash", provider="openai", client=oai_client, max_tokens=4096
    )

    class PipelineEmbeddings(BaseRagasEmbeddings):
        """Bọc embed_texts() của Task 4 để answer_relevancy dùng cùng
        embedding model với pipeline đang được đánh giá, thay vì model khác."""

        def embed_query(self, text: str) -> list[float]:
            return embed_texts([text])[0]

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return embed_texts(texts)

        async def aembed_query(self, text: str) -> list[float]:
            return self.embed_query(text)

        async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
            return self.embed_documents(texts)

    eval_emb = PipelineEmbeddings()

    runs = json.loads(RUNS_PATH.read_text(encoding="utf-8"))
    metric_names = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]

    all_scores: dict = {name: {} for name in CONFIGS}
    for config_name in CONFIGS:
        samples = [
            SingleTurnSample(
                user_input=row["question"],
                response=row[config_name]["answer"],
                retrieved_contexts=row[config_name]["retrieved_contexts"] or [""],
                reference=row["expected_answer"],
            )
            for row in runs
        ]
        metrics = [
            Faithfulness(llm=eval_llm),
            AnswerRelevancy(llm=eval_llm, embeddings=eval_emb),
            ContextRecall(llm=eval_llm),
            ContextPrecision(llm=eval_llm),
        ]
        print(f"\n=== Scoring {config_name} ({len(samples)} case) ===", flush=True)
        # max_workers mặc định 16 dội quá giới hạn RPM free-tier của Gemini,
        # khiến retry lặp im lặng (log_tenacity=False) kéo dài nhiều phút mỗi
        # job. Giảm song song, log retry để thấy tiến độ thật thay vì treo mù.
        run_config = RunConfig(
            max_workers=3, timeout=90, max_wait=20, max_retries=5, log_tenacity=True
        )
        result = evaluate(
            dataset=EvaluationDataset(samples=samples),
            metrics=metrics,
            run_config=run_config,
            raise_exceptions=False,
        )
        df = result.to_pandas()

        def cell(i: int, name: str):
            value = df.iloc[i][name]
            return None if (value is None or value != value) else float(value)  # NaN != NaN

        per_case = []
        for i, row in enumerate(runs):
            per_case.append(
                {
                    "case_index": row["case_index"],
                    "question": row["question"],
                    **{name: cell(i, name) for name in metric_names},
                }
            )
        # NaN xuất hiện khi raise_exceptions=False và job đó lỗi hẳn sau khi
        # hết retry; loại NaN trước khi tính trung bình để không lệch điểm.
        averages = {name: float(df[name].dropna().mean()) for name in metric_names}
        failed = {name: int(df[name].isna().sum()) for name in metric_names}
        all_scores[config_name] = {
            "per_case": per_case,
            "average": averages,
            "failed_count": failed,
        }
        print(f"  average: {averages}")
        print(f"  failed (NaN) per metric: {failed}")

    SCORES_PATH.write_text(json.dumps(all_scores, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved scores -> {SCORES_PATH}")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "all"
    if action in ("collect", "all"):
        collect()
    if action in ("score", "all"):
        score()
