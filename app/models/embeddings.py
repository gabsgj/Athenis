import os
import numpy as np
import hashlib
from typing import List

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
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
        if self.model:
            return self.model.encode(texts, convert_to_numpy=True)
        
        # Fallback to deterministic random vectors
        vectors = []
        for text in texts:
            seed = int(hashlib.sha256(text.encode('utf-8')).hexdigest(), 16) % (2**32)
            rng = np.random.default_rng(seed)
            vectors.append(rng.random(384, dtype=np.float32))
        return np.array(vectors)

    def search(self, query: str, corpus: List[str], top_k: int = 3):
        if not corpus:
            return []
        
        query_vec = self.embed([query])[0]
        corpus_vecs = self.embed(corpus)
        
        # Cosine similarity
        sim = np.dot(corpus_vecs, query_vec) / (np.linalg.norm(corpus_vecs, axis=1) * np.linalg.norm(query_vec))
        
        # Get top_k results
        top_indices = np.argsort(-sim)[:top_k]
        return [(i, sim[i]) for i in top_indices]

    def find_similar_risks(self, text: str):
        # This is a stub as per the instructions
        return []