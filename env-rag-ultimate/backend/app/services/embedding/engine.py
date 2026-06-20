"""
Embedding 引擎
"""
from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings


class EmbeddingEngine:
    def __init__(self, model_name=None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._embeddings = None
        self._init()

    def _init(self):
        print(f"[Embedding] 加载: {self.model_name}")
        if self.model_name.startswith("text-embedding"):
            self._embeddings = OpenAIEmbeddings(model=self.model_name, api_key=settings.OPENAI_API_KEY)
        else:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={"device": settings.EMBEDDING_DEVICE, "trust_remote_code": True},
                encode_kwargs={"normalize_embeddings": True, "batch_size": 32},
            )
        print("[Embedding] 加载完成")

    @property
    def embeddings(self):
        return self._embeddings


_engine = None

def get_embedding_engine() -> EmbeddingEngine:
    global _engine
    if _engine is None:
        _engine = EmbeddingEngine()
    return _engine
