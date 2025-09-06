#!/usr/bin/env python3
"""
File/text extractor CLI
Outputs JSON: {"text": "..."} on success or {"error": "..."} on failure.
Exit codes:
 0 - success
 1 - file not found
 2 - unsupported or extraction error
"""
import argparse
import json
import os
import sys
from typing import Optional

def extract_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_pdf(path: str) -> str:
    # lazy import to keep startup cheap and produce clearer errors if missing
    from pdfminer.high_level import extract_text
    return extract_text(path)

def extract_docx(path: str) -> str:
    # python-docx is imported as 'docx' and provides Document
    import docx
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text from .txt | .pdf | .docx and print JSON")
    parser.add_argument("--file", "-f", required=True, help="Path to input file")
    parser.add_argument("--collapse", action="store_true",
                        help="Collapse whitespace/newlines into single spaces")
    args = parser.parse_args()

    path = args.file
    if not os.path.exists(path):
        print(json.dumps({"error": "file_not_found"}))
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
            # fallback: try reading as text; if that fails, report unsupported
            try:
                text = extract_txt(path)
            except Exception:
                print(json.dumps({"error": f"unsupported_extension_{ext}"}))
                sys.exit(2)

        if args.collapse:
            text = " ".join(text.split())

        # Ensure the JSON is safe (no binary) and not too huge — still print it
        print(json.dumps({"text": text}))
        sys.exit(0)

    except Exception as e:
        # Return the exception message (useful for debugging), but keep compact JSON structure
        print(json.dumps({"error": str(e)}))
        sys.exit(2)

if __name__ == "__main__":
    main()
