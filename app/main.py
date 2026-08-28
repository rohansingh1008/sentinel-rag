from fastapi import FastAPI
from qdrant_client import QdrantClient

app = FastAPI()
client = QdrantClient(host="localhost", port=6333)

@app.get("/health")
def health():
    collections = client.get_collections()
    return {"status": "ok", "qdrant_collections": collections}