import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import json
from app.caching.semantic_cache import redis_client, CACHE_PREFIX

keys = redis_client.keys(f"{CACHE_PREFIX}*")
print(f"Found {len(keys)} cache keys with prefix '{CACHE_PREFIX}'")

for key in keys:
    print(f"\nKey: {key}")
    value = redis_client.get(key)
    if value:
        parsed = json.loads(value)
        print(f"  original_query: {parsed.get('original_query')}")
        print(f"  answer (first 100 chars): {parsed.get('answer', '')[:100]}")
    else:
        print("  (empty value)")