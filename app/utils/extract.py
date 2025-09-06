import sys
import os
import json
from io import BytesIO

from pdfminer.high_level import extract_text as pdf_extract
from docx import Document


def extract_from_pdf(path: str) -> str:
    return pdf_extract(path)


def extract_from_docx(path: str) -> str:
    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    args = ap.parse_args()
    path = args.file
    if not os.path.exists(path):
        print(json.dumps({"error": "not_found"}))
        sys.exit(1)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        text = extract_from_pdf(path)
    elif ext in (".docx",):
        text = extract_from_docx(path)
    elif ext in (".txt",):
        text = open(path, "r", encoding="utf-8", errors="ignore").read()
    else:
        print(json.dumps({"error": "unsupported"}))
        sys.exit(2)
    print(json.dumps({"text": text}))


if __name__ == "__main__":
    main()
