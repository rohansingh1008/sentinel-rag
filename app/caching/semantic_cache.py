import redis
import json
import numpy as np
from app.ingestion.embedder import embed_texts

# Connect to your existing Redis container
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

CACHE_PREFIX = "rag_cache:"
SIMILARITY_THRESHOLD = 0.92  # how close a new query must be to reuse a cached answer

def cosine_similarity(vec1, vec2):
    a, b = np.array(vec1), np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def get_cached_answer(query: str, user_role: str):
    """
    Checks if a semantically similar query (for the same role) was answered before.
    Returns the cached answer if found above the similarity threshold, else None.
    """
    query_vector = embed_texts([query])[0]

    # Scan all cached entries for this role (small scale — fine for a resume project)
    cache_keys = redis_client.keys(f"{CACHE_PREFIX}{user_role}:*")

    best_match = None
    best_score = 0.0

    for key in cache_keys:
        cached = json.loads(redis_client.get(key))
        score = cosine_similarity(query_vector, cached["embedding"])
        if score > best_score:
            best_score = score
            best_match = cached

    if best_match and best_score >= SIMILARITY_THRESHOLD:
        print(f"✅ Cache HIT (similarity: {best_score:.4f}) — skipping retrieval + generation")
        return best_match["answer"]

    print(f"❌ Cache MISS (best similarity: {best_score:.4f})")
    return None

def store_answer(query: str, user_role: str, answer: str):
    """Stores a query's embedding + answer in the cache for future reuse."""
    query_vector = embed_texts([query])[0]
    key = f"{CACHE_PREFIX}{user_role}:{hash(query)}"
    value = json.dumps({"embedding": query_vector, "answer": answer, "original_query": query})
    redis_client.set(key, value, ex=3600)  # expires after 1 hour