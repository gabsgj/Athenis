#!/usr/bin/env python3
"""
Extractor CLI — outputs JSON {"text": "..."} or {"error": "..."}.
Exit codes:
 0 success
 1 file not found
 2 extraction/unsupported error
"""
import argparse
import json
import os
import sys
from typing import Optional

MAX_DEFAULT = 5 * 1024 * 1024  # 5 MB default cap on output

def extract_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_pdf(path: str) -> str:
    from pdfminer.high_level import extract_text
    return extract_text(path)

def extract_docx(path: str) -> str:
    import docx
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def maybe_truncate(s: str, max_bytes: Optional[int]) -> str:
    if max_bytes is None:
        return s
    # truncate by bytes while keeping valid UTF-8
    b = s.encode("utf-8")[:max_bytes]
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        # drop incomplete tail
        return b.decode("utf-8", errors="ignore")

def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text from .txt | .pdf | .docx and print JSON")
    parser.add_argument("--file", "-f", required=True, help="Path to input file")
    parser.add_argument("--collapse", action="store_true", help="Collapse whitespace/newlines into single spaces")
    parser.add_argument("--max-bytes", type=int, default=MAX_DEFAULT,
                        help="Max output size in bytes (default 5MB). Use 0 for no limit.")
    args = parser.parse_args()

    path = args.file
    if not os.path.exists(path):
        print(json.dumps({"error": "file_not_found"}, ensure_ascii=False))
        sys.exit(1)

    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf":
            text = extract_pdf(path)
        elif ext == ".docx":
            text = extract_docx(path)
        elif ext == ".txt" or ext == "":
            text = extract_txt(path)
        else:
            # either try text or fail — here we try text first
            try:
                text = extract_txt(path)
            except Exception:
                print(json.dumps({"error": f"unsupported_extension_{ext}"}, ensure_ascii=False))
                sys.exit(2)

        if args.collapse:
            text = " ".join(text.split())

        max_bytes = None if args.max_bytes == 0 else args.max_bytes
        if max_bytes is not None:
            text = maybe_truncate(text, max_bytes)

        # Preserve Unicode characters
        print(json.dumps({"text": text}, ensure_ascii=False, separators=(",", ":")))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(2)

if __name__ == "__main__":
    main()
import re

# app/utils/extract.py

def split_into_clauses(text: str):
    """
    Stub implementation for testing.
    Splits text by periods or semicolons into simple clauses.
    """
    if not text:
        return []
    # Simple split: sentences ending with '.' or ';'
    clauses = [clause.strip() for clause in text.replace(';', '.').split('.') if clause.strip()]
    return clauses
