from sentence_transformers import CrossEncoder

reranker_model = CrossEncoder("BAAI/bge-reranker-base")

def rerank(query: str, candidates: list, top_k: int = 5):
    """
    Re-scores candidate (point, score) pairs using a cross-encoder that directly
    evaluates query-passage relevance, rather than trusting fused heuristic scores.
    """
    pairs = [(query, point.payload["text"]) for point, _ in candidates]
    rerank_scores = reranker_model.predict(pairs)

    reranked = list(zip([point for point, _ in candidates], rerank_scores))
    reranked.sort(key=lambda x: x[1], reverse=True)

    return reranked[:top_k]