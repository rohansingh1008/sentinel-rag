import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.reranker import rerank
from app.security.injection_guard import filter_safe_chunks
from app.generation.prompt_builder import build_prompt
from app.generation.llm_client import generate_answer

query = "What are noise models?"
user_role = "employee"

candidates = hybrid_search(query, top_k=10, vector_weight=0.75, user_role=user_role)
reranked = rerank(query, candidates, top_k=5)
safe_chunks = filter_safe_chunks(reranked)

print(f"\n=== DEBUG: {len(safe_chunks)} chunks reaching the prompt ===")
for point, score in safe_chunks:
    print(f"[{point.payload['source']}] {point.payload['text'][:100]}...")

prompt = build_prompt(query, safe_chunks)

print("\n=== DEBUG: Full prompt sent to LLM (first 1000 chars) ===")
print(prompt[:1000])

answer = generate_answer(prompt)

print("\n=== FINAL ANSWER ===")
print(answer)