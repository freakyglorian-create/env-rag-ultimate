"""
FastAPI 路由集成测试
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient


# ===== 测试客户端 =====

@pytest.fixture(autouse=True)
def mock_kb_load():
    """自动 mock 启动时的知识库加载，避免测试时加载真实模型"""
    with patch("app.api.routes.get_rag_engine") as mock_get:
        mock_engine = MagicMock()
        mock_engine.load_knowledge_base.return_value = True
        mock_engine.is_ready = True
        mock_get.return_value = mock_engine
        yield mock_get


@pytest.fixture
def client():
    import main as app_main
    return TestClient(app_main.app)


class TestStatusEndpoint:
    def test_status_ok(self, client):
        resp = client.get("/api/v1/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"
        assert "version" in data
        assert "available_models" in data

    def test_status_includes_embedding(self, client):
        resp = client.get("/api/v1/status")
        data = resp.json()
        assert "bge" in data["embedding_model"].lower()

    def test_status_includes_catalog(self, client):
        resp = client.get("/api/v1/status")
        data = resp.json()
        models = data["available_models"]
        assert len(models) > 0
        providers = {m["provider"] for m in models}
        assert "deepseek" in providers


class TestModelsEndpoint:
    def test_list_models(self, client):
        resp = client.get("/api/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 8  # 至少所有 provider 的模型

    def test_models_structure(self, client):
        resp = client.get("/api/v1/models")
        for item in resp.json():
            assert "provider" in item
            assert "model" in item
            assert "description" in item


class TestVerifyKeyEndpoint:
    @patch("app.api.routes.LLMFactory.verify_key")
    def test_valid_key(self, mock_verify, client):
        mock_verify.return_value = True
        resp = client.post("/api/v1/models/verify", json={
            "provider": "deepseek",
            "api_key": "sk-valid-key",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert len(data["models"]) > 0

    @patch("app.api.routes.LLMFactory.verify_key")
    def test_invalid_key(self, mock_verify, client):
        mock_verify.return_value = False
        resp = client.post("/api/v1/models/verify", json={
            "provider": "deepseek",
            "api_key": "sk-bad-key",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert data["models"] == []

    def test_empty_api_key_rejected(self, client):
        resp = client.post("/api/v1/models/verify", json={
            "provider": "deepseek",
            "api_key": "",
        })
        assert resp.status_code == 422


class TestQueryEndpoint:
    @patch("app.api.routes.get_rag_engine")
    def test_successful_query(self, mock_get_engine, client):
        from app.models.schemas import QueryResponse, SourceDocument

        mock_engine = MagicMock()
        mock_engine.is_ready = True
        mock_engine.query.return_value = QueryResponse(
            answer="SCR脱硝温度窗口为300-400°C。参考：02_大气污染控制.txt",
            sources=[SourceDocument(content="SCR脱硝温度300-400°C", source="02_大气污染控制.txt")],
            retrieval_time_ms=50.0, generation_time_ms=200.0, total_time_ms=250.0,
            provider_used="deepseek", model_used="deepseek-chat",
        )
        mock_get_engine.return_value = mock_engine

        resp = client.post("/api/v1/query", json={
            "question": "SCR脱硝温度？",
            "api_key": "sk-test",
            "provider": "deepseek",
            "use_query_rewrite": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "SCR" in data["answer"] or "300" in data["answer"]
        assert len(data["sources"]) >= 1

    @patch("app.api.routes.get_rag_engine")
    def test_kb_not_loaded(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.is_ready = True
        mock_engine.query.side_effect = ValueError("知识库未加载")
        mock_get_engine.return_value = mock_engine

        resp = client.post("/api/v1/query", json={
            "question": "test?",
            "api_key": "sk-test",
        })
        assert resp.status_code == 400

    def test_missing_api_key(self, client):
        resp = client.post("/api/v1/query", json={
            "question": "test?",
        })
        assert resp.status_code == 422

    def test_empty_question(self, client):
        resp = client.post("/api/v1/query", json={
            "question": "",
            "api_key": "sk-test",
        })
        assert resp.status_code == 422


class TestQueryStreamEndpoint:
    @patch("app.api.routes.get_rag_engine")
    def test_streaming_response(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.is_ready = True
        mock_engine.stream_query.return_value = iter([
            {"token": "SCR"},
            {"token": "脱硝"},
            {"sources": [{"content": "...", "source": "f.txt", "page": 1}], "done": True},
        ])
        mock_get_engine.return_value = mock_engine

        resp = client.post("/api/v1/query/stream", json={
            "question": "SCR脱硝？",
            "api_key": "sk-test",
        })
        assert resp.status_code == 200
        # SSE content type
        assert "text/event-stream" in resp.headers["content-type"]

    @patch("app.api.routes.get_rag_engine")
    def test_stream_kb_not_loaded(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.is_ready = False
        mock_get_engine.return_value = mock_engine

        resp = client.post("/api/v1/query/stream", json={
            "question": "test?",
            "api_key": "sk-test",
        })
        assert resp.status_code == 200
        # 流中的错误信息
        content_str = b""
        for chunk in resp.iter_bytes():
            content_str += chunk
        # JSON 中包含 error 字段，中文可能被 unicode 转义
        import json
        text = content_str.decode("utf-8")
        assert "error" in text


class TestUploadEndpoint:
    def test_unsupported_format(self, client):
        resp = client.post("/api/v1/upload", files={
            "file": ("test.png", b"fake image", "image/png"),
        })
        assert resp.status_code == 400

    def test_txt_upload(self, client, tmp_path, monkeypatch):
        import app.api.routes as routes_module
        # 使用测试目录作为上传目录
        monkeypatch.setattr(routes_module, "UPLOAD_DIR", tmp_path)

        resp = client.post("/api/v1/upload", files={
            "file": ("test.txt", "环境工程测试文档内容".encode("utf-8"), "text/plain"),
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["filename"] == "test.txt"


class TestKbEndpoints:
    @patch("app.api.routes.get_rag_engine")
    def test_build_kb(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.build_knowledge_base.return_value = {
            "chunks_count": 50, "documents_count": 6, "processing_time_ms": 1500.0,
        }
        mock_get_engine.return_value = mock_engine

        resp = client.post("/api/v1/kb/build")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["chunks_count"] == 50

    @patch("app.api.routes.get_rag_engine")
    def test_build_kb_error(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.build_knowledge_base.side_effect = Exception("build error")
        mock_get_engine.return_value = mock_engine

        resp = client.post("/api/v1/kb/build")
        assert resp.status_code == 500

    @patch("app.api.routes.get_rag_engine")
    def test_load_kb_success(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.load_knowledge_base.return_value = True
        mock_get_engine.return_value = mock_engine

        resp = client.post("/api/v1/kb/load")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @patch("app.api.routes.get_rag_engine")
    def test_load_kb_not_found(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.load_knowledge_base.return_value = False
        mock_get_engine.return_value = mock_engine

        resp = client.post("/api/v1/kb/load")
        assert resp.status_code == 404

    def test_list_documents(self, client):
        resp = client.get("/api/v1/kb/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for item in data:
            assert "name" in item
            assert "size" in item


class TestEvaluationEndpoints:
    @patch("app.api.routes.get_evaluator")
    def test_run_eval(self, mock_get_evaluator, client):
        mock_eval = MagicMock()
        mock_eval.run_evaluation.return_value = {
            "total_questions": 2, "evaluated": 2,
            "average_scores": {"overall": 0.85},
            "per_question": [],
            "generated_at": "2024-01-01T00:00:00",
        }
        mock_get_evaluator.return_value = mock_eval

        resp = client.post("/api/v1/evaluation/run", json={
            "provider": "deepseek",
            "api_key": "sk-test",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_questions"] == 2

    @patch("app.api.routes.get_evaluator")
    def test_run_eval_error(self, mock_get_evaluator, client):
        mock_eval = MagicMock()
        mock_eval.run_evaluation.side_effect = Exception("eval error")
        mock_get_evaluator.return_value = mock_eval

        resp = client.post("/api/v1/evaluation/run", json={
            "provider": "deepseek",
            "api_key": "sk-test",
        })
        assert resp.status_code == 500

    @patch("app.api.routes.get_evaluator")
    def test_get_report(self, mock_get_evaluator, client):
        mock_eval = MagicMock()
        mock_eval.get_latest_report.return_value = {
            "total_questions": 12, "evaluated": 12, "average_scores": {"overall": 0.78},
        }
        mock_get_evaluator.return_value = mock_eval

        resp = client.get("/api/v1/evaluation/report")
        assert resp.status_code == 200
        assert resp.json()["total_questions"] == 12

    @patch("app.api.routes.get_evaluator")
    def test_get_report_none(self, mock_get_evaluator, client):
        mock_eval = MagicMock()
        mock_eval.get_latest_report.return_value = None
        mock_get_evaluator.return_value = mock_eval

        resp = client.get("/api/v1/evaluation/report")
        assert resp.status_code == 200
        assert resp.json() is None
