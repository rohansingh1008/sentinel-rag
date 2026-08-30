import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import time
import json

from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.reranker import rerank
from app.security.injection_guard import filter_safe_chunks, scan_for_injection
from app.generation.prompt_builder import build_prompt
from app.generation.llm_client import generate_answer
from app.caching.semantic_cache import get_cached_answer, store_answer, redis_client, CACHE_PREFIX

st.set_page_config(page_title="Sentinel-RAG", layout="wide")

st.title("🛡️ Sentinel-RAG")
st.caption("Secure, token-efficient Retrieval-Augmented Generation")

tab_chat, tab_eval, tab_cache = st.tabs(["💬 Chat", "📊 Evaluation", "⚡ Cache Stats"])

# ============ TAB 1: CHAT ============
with tab_chat:
    st.sidebar.header("Settings")
    user_role = st.sidebar.selectbox("Simulated user role", ["guest", "employee", "admin"])
    st.sidebar.markdown(f"**Access level:** `{user_role}`")
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "- `guest` → public only\n"
        "- `employee` → public + internal\n"
        "- `admin` → public + internal + confidential"
    )

    query = st.text_input("Ask a question:", placeholder="e.g. What are noise models?")

    if st.button("Ask", type="primary") and query:
        start_time = time.time()
        cached = get_cached_answer(query, user_role)

        if cached:
            elapsed = time.time() - start_time
            st.success(f"✅ Cache HIT — answered in {elapsed:.2f}s")
            st.markdown("### Answer")
            st.write(cached)
        else:
            with st.spinner("Retrieving relevant documents..."):
                candidates = hybrid_search(query, top_k=10, vector_weight=0.75, user_role=user_role)
                reranked = rerank(query, candidates, top_k=5)

            with st.expander(f"📄 Retrieved chunks ({len(reranked)}) — before injection guard"):
                for i, (point, score) in enumerate(reranked):
                    flagged = scan_for_injection(point.payload["text"])["flagged"]
                    flag_icon = "🚩" if flagged else "✅"
                    st.markdown(f"**{i+1}. {flag_icon} [{point.payload['source']}]** (score: {score:.3f})")
                    st.text(point.payload["text"][:200] + "...")

            safe_chunks = filter_safe_chunks(reranked)
            removed_count = len(reranked) - len(safe_chunks)
            if removed_count > 0:
                st.warning(f"⚠️ {removed_count} chunk(s) removed by the injection guard before generation.")

            with st.spinner("Generating answer..."):
                prompt = build_prompt(query, safe_chunks)
                answer = generate_answer(prompt)
                store_answer(query, user_role, answer)

            elapsed = time.time() - start_time
            st.info(f"❌ Cache MISS — answered in {elapsed:.2f}s")
            st.markdown("### Answer")
            st.write(answer)

            with st.expander("📚 Sources used"):
                for i, (point, score) in enumerate(safe_chunks):
                    st.markdown(f"**[Source {i+1}]** {point.payload['source']}")

# ============ TAB 2: EVALUATION ============
with tab_eval:
    st.header("Evaluation Results")
    eval_path = os.path.join(os.path.dirname(__file__), "..", "app", "evaluation", "eval_results.csv")

    if os.path.exists(eval_path):
        df = pd.read_csv(eval_path)

        col1, col2 = st.columns(2)
        col1.metric("Average Faithfulness", f"{df['faithfulness_score'].mean():.2f}")
        col2.metric("Average Relevance", f"{df['relevance_score'].mean():.2f}")

        st.markdown("### Per-question scores")
        st.dataframe(
            df[["question", "faithfulness_score", "relevance_score"]],
            use_container_width=True,
        )

        st.markdown("### Score comparison")
        chart_df = df[["question", "faithfulness_score", "relevance_score"]].set_index("question")
        st.bar_chart(chart_df)

        with st.expander("Full details (including judge reasoning)"):
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No evaluation results found. Run `python -m app.evaluation.run_eval` first.")


# ============ TAB 3: CACHE STATS ============
with tab_cache:
    st.header("Semantic Cache Stats")

    try:
        all_keys = redis_client.keys(f"{CACHE_PREFIX}*")
        st.metric("Total cached entries", len(all_keys))

        role_counts = {}
        for key in all_keys:
            parts = key.split(":")
            if len(parts) >= 2:
                role = parts[1]
                role_counts[role] = role_counts.get(role, 0) + 1

        if role_counts:
            st.markdown("### Cached entries by role")
            st.bar_chart(role_counts)

        st.markdown("### Cached queries")
        if all_keys:
            for key in all_keys[:20]:
                raw_value = redis_client.get(key)
                if raw_value:
                    cached = json.loads(raw_value)
                    with st.expander(f"🔑 {cached.get('original_query', key)}"):
                        st.write(cached["answer"])
        else:
            st.info("No cached queries yet. Ask a question in the Chat tab first.")

        if st.button("Clear cache"):
            for key in all_keys:
                redis_client.delete(key)
            st.success("Cache cleared. Refresh the page to see updated stats.")

    except Exception as e:
        st.error(f"Error loading cache stats: {e}")