import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.ingestion.indexer import client, COLLECTION_NAME
from app.security.acl_filter import build_acl_filter

print("=== Checking injection_test.txt ===")
points, _ = client.scroll(collection_name=COLLECTION_NAME, limit=500)
for p in points:
    if p.payload['source'] == 'injection_test.txt':
        print("source:", p.payload['source'])
        print("access_level (repr):", repr(p.payload['access_level']))
        print("text preview:", p.payload['text'][:100])
        print("---")

print("\n=== Total points by access level ===")
from collections import Counter
levels = Counter(p.payload.get('access_level', 'MISSING') for p in points)
print(levels)

print("\n=== ACL filter for guest ===")
print(build_acl_filter("guest"))

print("\n=== Manual scroll test with guest filter ===")
guest_filter = build_acl_filter("guest")
filtered_points, _ = client.scroll(collection_name=COLLECTION_NAME, scroll_filter=guest_filter, limit=500)
print(f"Guest can see {len(filtered_points)} chunks total")
for p in filtered_points:
    print(f"  - [{p.payload['source']}] access={p.payload['access_level']}")