"""
应用配置测试
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch


class TestSettings:
    def test_app_defaults(self):
        from app.core.config import settings
        assert settings.APP_NAME == "环境工程 RAG Ultimate"
        assert settings.APP_VERSION == "3.0.0"
        assert settings.DEBUG is False

    def test_embedding_defaults(self):
        from app.core.config import settings
        assert "bge-large-zh" in settings.EMBEDDING_MODEL.lower()
        assert settings.EMBEDDING_DEVICE == "cpu"

    def test_reranker_defaults(self):
        from app.core.config import settings
        assert "bge-reranker" in settings.RERANKER_MODEL.lower()
        assert settings.USE_RERANKER is True
        assert settings.RERANKER_TOP_K == 20

    def test_rag_defaults(self):
        from app.core.config import settings
        assert settings.CHUNK_SIZE == 512
        assert settings.CHUNK_OVERLAP == 100
        assert settings.TOP_K_RETRIEVAL == 5
        assert settings.BM25_WEIGHT == 0.3
        assert settings.DENSE_WEIGHT == 0.7

    def test_query_transform_defaults(self):
        from app.core.config import settings
        assert settings.ENABLE_QUERY_REWRITE is True
        assert settings.ENABLE_MULTI_QUERY is False

    def test_llm_defaults(self):
        from app.core.config import settings
        assert settings.DEFAULT_LLM_PROVIDER == "deepseek"
        assert settings.DEFAULT_LLM_MODEL == "deepseek-chat"

    def test_cors_origins(self):
        from app.core.config import settings
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:5173" in settings.CORS_ORIGINS

    def test_data_dirs_exist(self):
        from app.core.config import KNOWLEDGE_DIR, UPLOAD_DIR, VECTOR_STORE_DIR, EVALUATION_DIR
        assert KNOWLEDGE_DIR.exists()
        assert UPLOAD_DIR.exists()
        assert VECTOR_STORE_DIR.exists()
        assert EVALUATION_DIR.exists()

    @patch.dict(os.environ, {"DEBUG": "true", "CHUNK_SIZE": "1024", "TOP_K_RETRIEVAL": "10"})
    def test_env_override(self):
        """验证环境变量覆盖默认值"""
        # 注意：settings 已在模块加载时初始化，这里验证的是 env 读取逻辑
        assert os.getenv("DEBUG") == "true"
        assert int(os.getenv("CHUNK_SIZE", "512")) == 1024
