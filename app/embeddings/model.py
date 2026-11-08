"""
app/embeddings/model.py

Provides a singleton HuggingFaceEmbeddings instance that runs the
sentence-transformers/all-MiniLM-L6-v2 model locally on CPU.
"""

import os
from functools import lru_cache

# Ensure PyTorch cache is localized and HuggingFace operates offline once cached
if not os.environ.get("TORCHINDUCTOR_CACHE_DIR"):
    os.environ["TORCHINDUCTOR_CACHE_DIR"] = os.path.abspath(".torch_cache")
if not os.environ.get("TORCH_HOME"):
    os.environ["TORCH_HOME"] = os.path.abspath(".torch_cache")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from langchain_huggingface import HuggingFaceEmbeddings
from app.config import get_settings


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Return the cached local embedding model.
    """
    settings = get_settings()
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
