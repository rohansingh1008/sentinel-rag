import sys, os, hashlib
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.ingestion.loader import load_documents_from_folder
from app.ingestion.chunker import chunk_text
from app.ingestion.embedder import embed_texts
from app.ingestion.indexer import (
    create_collection, index_chunks,
    load_ingested_files, save_ingested_files
)
from app.ingestion.pii_redactor import redact_pii

ACCESS_MAP = {
    "sample.txt": "internal",
    "sample2.txt": "public",
    "sample-local-pdf.pdf": "confidential",
    "resource1.pdf": "internal",
    "injection_test.txt": "public"
}

def file_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

create_collection()

docs = load_documents_from_folder("data")
ingested = load_ingested_files()
total_chunks = 0

for filename, text in docs:
    current_hash = file_hash(text)

    if ingested.get(filename) == current_hash:
        print(f"Skipping {filename} (already ingested, unchanged).")
        continue

    print(f"Processing {filename}...")
    text = redact_pii(text)
    chunks = chunk_text(text)
    embeddings = embed_texts(chunks)
    access_level = ACCESS_MAP.get(filename, "public")
    index_chunks(chunks, embeddings, source=filename, access_level=access_level)
    total_chunks += len(chunks)
    ingested[filename] = current_hash
    print(f"Indexed {len(chunks)} chunks from {filename} (access: {access_level})")

save_ingested_files(ingested)
print(f"\nNewly indexed: {total_chunks} chunks. Total tracked files: {len(ingested)}")