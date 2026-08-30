import sys, os, time
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.reranker import rerank
from app.security.injection_guard import filter_safe_chunks
from app.generation.prompt_builder import build_prompt
from app.generation.llm_client import generate_answer
from app.caching.semantic_cache import get_cached_answer, store_answer

def answer_query(query: str, user_role: str = "employee"):
    cached = get_cached_answer(query, user_role)
    if cached:
        return cached

    candidates = hybrid_search(query, top_k=10, vector_weight=0.75, user_role=user_role)
    reranked = rerank(query, candidates, top_k=5)
    safe_chunks = filter_safe_chunks(reranked)
    prompt = build_prompt(query, safe_chunks)
    answer = generate_answer(prompt)

    store_answer(query, user_role, answer)
    return answer

# Test: same query twice, then a paraphrased version
queries = [
    "What are noise models?",
    "What are noise models?",              # exact repeat — should hit cache
    "Can you explain what noise models are?",  # paraphrase — should also hit cache
]

for q in queries:
    print(f"\n>>> Query: {q}")
    start = time.time()
    answer = answer_query(q)
    elapsed = time.time() - start
    print(f"(took {elapsed:.2f}s)")
    print(answer[:200])