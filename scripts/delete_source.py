import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.ingestion.indexer import delete_by_source

delete_by_source("resource1.pdf")
print("Deleted old resource1.pdf points.")