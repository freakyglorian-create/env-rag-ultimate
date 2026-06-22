"""
环境工程 RAG Ultimate 系统配置
API Key 由前端用户传入，不再存储在服务端 .env 中
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ===== HuggingFace 离线模式（必须在 load_dotenv 之前设置）=====
# 优先使用 HF Mirror，避免超时
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_OFFLINE", "0")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")

load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR.parent / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge_base"
UPLOAD_DIR = DATA_DIR / "uploads"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
EVALUATION_DIR = DATA_DIR / "evaluation"

for d in [KNOWLEDGE_DIR, UPLOAD_DIR, VECTOR_STORE_DIR, EVALUATION_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    APP_NAME: str = "环境工程 RAG Ultimate"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ===== Default LLM（仅作为回退默认值）=====
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "deepseek")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "deepseek-chat")

    # ===== Embedding =====
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")

    # ===== Reranker =====
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
    USE_RERANKER: bool = os.getenv("USE_RERANKER", "true").lower() == "true"
    RERANKER_TOP_K: int = int(os.getenv("RERANKER_TOP_K", "20"))

    # ===== Query Transform =====
    ENABLE_QUERY_REWRITE: bool = os.getenv("ENABLE_QUERY_REWRITE", "true").lower() == "true"
    ENABLE_MULTI_QUERY: bool = os.getenv("ENABLE_MULTI_QUERY", "false").lower() == "true"

    # ===== RAG =====
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    BM25_WEIGHT: float = float(os.getenv("BM25_WEIGHT", "0.3"))
    DENSE_WEIGHT: float = float(os.getenv("DENSE_WEIGHT", "0.7"))

    # ===== Evaluation =====
    EVALUATION_DATASET_PATH: str = str(EVALUATION_DIR / "golden_set.json")
    VECTOR_STORE_PATH: Path = VECTOR_STORE_DIR

    # ===== CORS =====
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
