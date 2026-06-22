"""
Pydantic 数据模型测试
"""
import pytest
from pydantic import ValidationError
from app.models.schemas import (
    LLMProvider, LLMConfig, QueryRequest, QueryResponse,
    SourceDocument, BuildKBResponse, UploadResponse,
    SystemStatus, ModelInfo, VerifyKeyRequest, VerifyKeyResponse,
    EvalRequest,
)


class TestLLMProvider:
    def test_provider_values(self):
        assert LLMProvider.DEEPSEEK == "deepseek"
        assert LLMProvider.QWEN == "qwen"
        assert LLMProvider.GLM == "glm"
        assert LLMProvider.KIMI == "kimi"

    def test_provider_from_string(self):
        assert LLMProvider("deepseek") == LLMProvider.DEEPSEEK
        assert LLMProvider("qwen") == LLMProvider.QWEN

    def test_invalid_provider(self):
        with pytest.raises(ValueError):
            LLMProvider("invalid")


class TestLLMConfig:
    def test_minimal_config(self):
        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        assert cfg.provider == LLMProvider.DEEPSEEK
        assert cfg.model is None
        assert cfg.api_key == "sk-test"

    def test_full_config(self):
        cfg = LLMConfig(provider=LLMProvider.QWEN, model="qwen-max", api_key="sk-abc")
        assert cfg.model == "qwen-max"

    def test_api_key_repr_masked(self):
        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-secret-123")
        r = repr(cfg)
        assert "sk-secret-123" not in r
        assert "***" in r

    def test_empty_api_key_rejected(self):
        with pytest.raises(ValidationError):
            LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="")

    def test_missing_api_key(self):
        with pytest.raises(ValidationError):
            LLMConfig(provider=LLMProvider.DEEPSEEK)

    def test_provider_as_string(self):
        cfg = LLMConfig(provider="deepseek", api_key="sk-test")  # type: ignore
        assert cfg.provider == LLMProvider.DEEPSEEK


class TestQueryRequest:
    def test_minimal_request(self):
        req = QueryRequest(question="什么是MBR工艺？", api_key="sk-test")
        assert req.question == "什么是MBR工艺？"
        assert req.top_k == 5  # default
        assert req.provider == LLMProvider.DEEPSEEK  # default
        assert req.use_reranker is True
        assert req.use_query_rewrite is True
        assert req.use_multi_query is False

    def test_full_request(self):
        req = QueryRequest(
            question="SCR脱硝温度？",
            top_k=10,
            provider=LLMProvider.QWEN,
            model="qwen-plus",
            api_key="sk-abc",
            use_reranker=False,
            use_query_rewrite=False,
            use_multi_query=True,
        )
        assert req.top_k == 10
        assert req.model == "qwen-plus"
        assert req.use_multi_query is True

    def test_empty_question_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="", api_key="sk-test")

    def test_question_too_long(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="x" * 2001, api_key="sk-test")

    def test_top_k_min(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="test", top_k=0, api_key="sk-test")

    def test_top_k_max(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="test", top_k=21, api_key="sk-test")

    def test_default_model_is_none(self):
        req = QueryRequest(question="test", api_key="sk-test")
        assert req.model is None


class TestSourceDocument:
    def test_minimal(self):
        sd = SourceDocument(content="test content", source="file.txt")
        assert sd.page == 1
        assert sd.score is None
        assert sd.chunk_id is None

    def test_full(self):
        sd = SourceDocument(content="test", source="file.txt", page=5, score=0.95, chunk_id="chunk-1")
        assert sd.page == 5
        assert sd.score == 0.95


class TestQueryResponse:
    def test_minimal_response(self):
        resp = QueryResponse(answer="test answer", sources=[])
        assert resp.answer == "test answer"
        assert resp.provider_used == ""
        assert resp.model_used == ""

    def test_full_response(self):
        sources = [SourceDocument(content="ctx", source="f.txt")]
        resp = QueryResponse(
            answer="ans", sources=sources,
            retrieval_time_ms=100.5, generation_time_ms=500.0,
            total_time_ms=600.5, provider_used="deepseek",
            model_used="deepseek-chat", query_rewrite="rewritten query",
            multi_queries=["q1", "q2"],
        )
        assert resp.total_time_ms == 600.5
        assert len(resp.multi_queries) == 2


class TestBuildKBResponse:
    def test_valid(self):
        resp = BuildKBResponse(
            success=True, message="done",
            chunks_count=100, documents_count=6, processing_time_ms=1500.0,
        )
        assert resp.success is True


class TestUploadResponse:
    def test_valid(self):
        resp = UploadResponse(success=True, filename="doc.pdf", size=1024, file_type=".pdf")
        assert resp.file_type == ".pdf"


class TestSystemStatus:
    def test_valid(self):
        status = SystemStatus(
            status="running", version="3.0.0",
            knowledge_base_loaded=True, embedding_model="BAAI/bge-large-zh-v1.5",
            reranker_enabled=True, query_rewrite_enabled=True,
            multi_query_enabled=False, available_models=[],
        )
        assert status.status == "running"


class TestVerifyKeyRequest:
    def test_valid(self):
        req = VerifyKeyRequest(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        assert req.provider == LLMProvider.DEEPSEEK

    def test_empty_key_rejected(self):
        with pytest.raises(ValidationError):
            VerifyKeyRequest(provider=LLMProvider.DEEPSEEK, api_key="")


class TestVerifyKeyResponse:
    def test_valid_key(self):
        resp = VerifyKeyResponse(valid=True, models=["deepseek-chat"], message="有效")
        assert resp.valid is True

    def test_invalid_key(self):
        resp = VerifyKeyResponse(valid=False, models=[], message="无效")
        assert resp.valid is False


class TestEvalRequest:
    def test_minimal(self):
        req = EvalRequest(api_key="sk-test")
        assert req.provider == LLMProvider.DEEPSEEK
        assert req.model is None

    def test_custom_provider(self):
        req = EvalRequest(provider=LLMProvider.GLM, model="glm-4", api_key="sk-test")
        assert req.model == "glm-4"
