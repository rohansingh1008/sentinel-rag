import uuid
import os
import json
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "documents"
TRACKING_FILE = "data/.ingested_files.json"


def delete_by_source(source: str):
    """Deletes all points belonging to a specific source file."""
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="source", match=MatchValue(value=source))]
        ),
    )

def create_collection():
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

def reset_collection():
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
    create_collection()
    if os.path.exists(TRACKING_FILE):
        os.remove(TRACKING_FILE)  # clear tracking too, since data is gone

def index_chunks(chunks: list[str], embeddings: list[list[float]], source: str, access_level: str = "public"):
    access_level = access_level.strip().lower()  # defensive normalization
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"text": chunk, "source": source, "access_level": access_level},
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)

def load_ingested_files() -> dict:
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, "r") as f:
            return json.load(f)
    return {}

def save_ingested_files(tracking: dict):
    with open(TRACKING_FILE, "w") as f:
        json.dump(tracking, f, indent=2)