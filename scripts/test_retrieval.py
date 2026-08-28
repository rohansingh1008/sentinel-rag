import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.retrieval.hybrid_search import vector_search, bm25_search, hybrid_search
from app.retrieval.reranker import rerank
from app.security.injection_guard import filter_safe_chunks

query = "What is the refund policy?"
user_role = "guest"

candidates = hybrid_search(query, top_k=10, vector_weight=0.75, user_role=user_role)
reranked = rerank(query, candidates, top_k=5)

print("=== BEFORE INJECTION GUARD ===")
for i, (point, score) in enumerate(reranked):
    print(f"{i+1}. [{point.payload['source']}] {point.payload['text'][:80]}...")

safe_chunks = filter_safe_chunks(reranked)

print("\n=== AFTER INJECTION GUARD ===")
for i, (point, score) in enumerate(safe_chunks):
    print(f"{i+1}. [{point.payload['source']}] {point.payload['text'][:80]}...")