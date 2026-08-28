import os
from pypdf import PdfReader

def load_text_file(filepath: str) -> str:
    encodings_to_try = ["utf-8", "cp1252", "latin-1"]
    for encoding in encodings_to_try:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def load_pdf_file(filepath: str) -> str:
    """Extracts text from a PDF file, page by page."""
    reader = PdfReader(filepath)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts)

def load_documents_from_folder(folder_path: str) -> list[tuple[str, str]]:
    docs = []
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if filename.endswith(".txt"):
            docs.append((filename, load_text_file(filepath)))
        elif filename.endswith(".pdf"):
            docs.append((filename, load_pdf_file(filepath)))
    return docs