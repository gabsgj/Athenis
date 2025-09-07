import os
import numpy as np
from typing import List

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


class Embedder:
    def __init__(self):
        self.model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.model = None
        if SentenceTransformer:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception:
                self.model = None

    def embed(self, texts: List[str]) -> np.ndarray:
        if self.model is None:
            # Simple fallback: hash-based pseudo-embeddings
            arr = []
            for t in texts:
                rng = np.random.default_rng(abs(hash(t)) % (2**32))
                arr.append(rng.standard_normal(384))
            return np.array(arr)
        return np.array(self.model.encode(texts, convert_to_numpy=True))

    def search(self, query: str, corpus: List[str], top_k: int = 5):
        if not corpus:
            return []
        all_texts = [query] + corpus
        embs = self.embed(all_texts)
        q = embs[0]
        docs = embs[1:]
        sims = docs @ q / (np.linalg.norm(docs, axis=1) * np.linalg.norm(q) + 1e-9)
        idxs = np.argsort(-sims)[:top_k]
        return [(int(i), float(sims[i])) for i in idxs]
     # 🔹 Stub for risk_detector
    def find_similar_risks(self, text: str):
        # Return empty list or dummy results for testing
        return []