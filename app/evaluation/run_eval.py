import json
import os
import csv

from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.reranker import rerank
from app.security.injection_guard import filter_safe_chunks
from app.generation.prompt_builder import build_prompt
from app.generation.llm_client import generate_answer
from app.evaluation.evaluator import evaluate_faithfulness, evaluate_relevance


def load_golden_dataset():
    path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    with open(path, "r") as f:
        return json.load(f)


def run_pipeline(query: str, user_role: str):
    candidates = hybrid_search(query, top_k=10, vector_weight=0.75, user_role=user_role)
    reranked = rerank(query, candidates, top_k=5)
    safe_chunks = filter_safe_chunks(reranked)
    prompt = build_prompt(query, safe_chunks)
    answer = generate_answer(prompt)
    contexts = [point.payload["text"] for point, _ in safe_chunks]
    return answer, contexts


def main():
    golden = load_golden_dataset()
    results = []

    for item in golden:
        print(f"\nEvaluating: {item['question']}")
        answer, contexts = run_pipeline(item["question"], item["user_role"])

        faithfulness = evaluate_faithfulness(answer, contexts)
        relevance = evaluate_relevance(item["question"], answer)

        print(f"  Faithfulness: {faithfulness['score']} — {faithfulness['reason']}")
        print(f"  Relevance:    {relevance['score']} — {relevance['reason']}")

        results.append({
            "question": item["question"],
            "answer": answer,
            "faithfulness_score": faithfulness["score"],
            "faithfulness_reason": faithfulness["reason"],
            "relevance_score": relevance["score"],
            "relevance_reason": relevance["reason"],
        })

    avg_faithfulness = sum(r["faithfulness_score"] for r in results) / len(results)
    avg_relevance = sum(r["relevance_score"] for r in results) / len(results)

    print(f"\n=== SUMMARY ===")
    print(f"Average Faithfulness: {avg_faithfulness:.2f}")
    print(f"Average Relevance:    {avg_relevance:.2f}")

    out_path = os.path.join(os.path.dirname(__file__), "eval_results.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved results to {out_path}")


if __name__ == "__main__":
    main()