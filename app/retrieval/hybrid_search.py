from rank_bm25 import BM25Okapi
from app.ingestion.embedder import embed_texts
from app.ingestion.indexer import client, COLLECTION_NAME
from app.security.acl_filter import build_acl_filter

# Per-role BM25 cache — different roles see different corpora, so we can't share one cache
_bm25_cache = {}  # { role: (bm25_index, points) }


def vector_search(query: str, top_k: int = 5, user_role: str = "guest"):
    """Semantic search using embedding similarity, filtered by role."""
    query_vector = embed_texts([query])[0]
    acl_filter = build_acl_filter(user_role)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=acl_filter,
        limit=top_k,
    )
    return results.points


def get_all_chunks(user_role: str = "guest"):
    """Fetches stored chunks the given role is permitted to see."""
    acl_filter = build_acl_filter(user_role)
    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=acl_filter,
        limit=10000,
    )
    return points


def build_bm25_index(user_role: str = "guest"):
    """Builds and caches the BM25 index for a specific role's permitted data."""
    points = get_all_chunks(user_role)
    corpus = [p.payload["text"] for p in points]
    tokenized_corpus = [doc.lower().split() for doc in corpus]

    bm25 = BM25Okapi(tokenized_corpus)
    _bm25_cache[user_role] = (bm25, points)
    print(f"BM25 index built and cached for role '{user_role}' ({len(points)} chunks).")
    return bm25, points


def get_bm25_index(user_role: str = "guest"):
    """Returns cached BM25 index for a role, building it if not already cached."""
    if user_role not in _bm25_cache:
        return build_bm25_index(user_role)
    return _bm25_cache[user_role]


def bm25_search(query: str, top_k: int = 5, user_role: str = "guest"):
    """Keyword-based search using the cached, role-filtered BM25 index."""
    bm25, points = get_bm25_index(user_role)
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    scored_points = list(zip(points, scores))
    scored_points.sort(key=lambda x: x[1], reverse=True)

    return scored_points[:top_k]


def refresh_bm25_index(user_role: str = "guest"):
    """Call this after new documents are ingested, to rebuild a role's cache."""
    return build_bm25_index(user_role)


def hybrid_search(query: str, top_k: int = 5, vector_weight: float = 0.5, user_role: str = "guest"):
    """
    Combines vector and BM25 results using weighted score fusion.
    vector_weight: 0.0 = pure BM25, 1.0 = pure vector, 0.5 = balanced
    Both underlying searches are role-filtered, so results respect ACL.
    """
    vector_results = vector_search(query, top_k=top_k * 2, user_role=user_role)
    bm25_results = bm25_search(query, top_k=top_k * 2, user_role=user_role)

    vector_scores = {p.id: p.score for p in vector_results}

    bm25_raw_scores = [score for _, score in bm25_results]
    max_bm25 = max(bm25_raw_scores) if bm25_raw_scores else 1
    min_bm25 = min(bm25_raw_scores) if bm25_raw_scores else 0
    bm25_range = max_bm25 - min_bm25 if max_bm25 != min_bm25 else 1

    bm25_scores = {
        p.id: (score - min_bm25) / bm25_range
        for p, score in bm25_results
    }

    all_points = {p.id: p for p in vector_results}
    all_points.update({p.id: p for p, _ in bm25_results})

    combined_scores = []
    for point_id, point in all_points.items():
        v_score = vector_scores.get(point_id, 0)
        b_score = bm25_scores.get(point_id, 0)
        final_score = (vector_weight * v_score) + ((1 - vector_weight) * b_score)
        combined_scores.append((point, final_score))

    combined_scores.sort(key=lambda x: x[1], reverse=True)
    return combined_scores[:top_k]