import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.ingestion.indexer import client, COLLECTION_NAME

points, _ = client.scroll(collection_name=COLLECTION_NAME, limit=200)
for p in points:
    if p.payload['source'] == 'resource1.pdf':
        print(p.payload['access_level'])
        break