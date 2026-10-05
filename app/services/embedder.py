"""The one place the embedding model is loaded from.

The model is fetched from the Hugging Face Hub, pinned to an exact commit so a
change upstream can't silently change (or compromise) what gets loaded. The
corpus vectors in app/data/embeddings were produced by this revision; queries
must be embedded by the same one or search quality silently degrades.
"""
from typing import Optional

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def load_embedder(device: Optional[str] = None) -> SentenceTransformer:
    return SentenceTransformer(
        EMBEDDING_MODEL, revision=EMBEDDING_MODEL_REVISION, device=device
    )
