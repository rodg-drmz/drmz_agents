# 📄 text_extractor.py
# Extracts plain text from PDFs

from PyPDF2 import PdfReader

def extract_text_from_pdf(file_path: str) -> str:
    with open(file_path, "rb") as f:
        reader = PdfReader(f)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
