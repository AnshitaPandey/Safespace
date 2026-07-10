"""
Embedding generation for the RAG memory system. Uses a small local sentence-transformer
(all-MiniLM-L6-v2, 384-dim) rather than a hosted embeddings API — good enough quality for
short memory/journal snippets, no external API dependency or per-call cost, and fast enough
on CPU for this workload.
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    # Loaded once per process and cached — loading it per-call would dominate latency.
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_text(text: str) -> list[float]:
    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()
