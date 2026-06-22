"""
RAG 核心引擎测试
"""
import pytest
from unittest.mock import patch, MagicMock

from app.models.schemas import LLMConfig, LLMProvider, QueryResponse
from app.services.rag.engine import RAGEngine, get_rag_engine, ENV_PROMPT


class TestRAGEngineInit:
    def test_initial_state(self):
        engine = RAGEngine()
        assert engine.is_ready is False

    def test_singleton(self):
        # 注意：单例测试可能受其他测试影响
        e1 = RAGEngine()
        e2 = RAGEngine()
        assert e1 is not e2  # 新建实例不是单例
        # get_rag_engine 返回的是模块级单例
        from app.services.rag.engine import _engine
        import app.services.rag.engine as eng_mod
        eng_mod._engine = None  # 重置
        g1 = get_rag_engine()
        g2 = get_rag_engine()
        assert g1 is g2


class TestLoadKnowledgeBase:
    def test_load_success(self):
        engine = RAGEngine()
        engine.search = MagicMock()
        result = engine.load_knowledge_base()
        assert result is True
        assert engine.is_ready is True

    def test_load_failure(self):
        engine = RAGEngine()
        engine.search = MagicMock()
        engine.search.load_index.side_effect = FileNotFoundError("no index")
        result = engine.load_knowledge_base()
        assert result is False
        assert engine.is_ready is False


class TestBuildKnowledgeBase:
    @patch("app.services.rag.engine.DocumentParser")
    def test_build_success(self, mock_parser):
        from langchain_core.documents import Document

        engine = RAGEngine()
        engine.search = MagicMock()

        mock_parser.parse_directory.return_value = [Document(page_content="test", metadata={"source": "f.txt"})]
        mock_parser.split_documents.return_value = [Document(page_content="test chunk", metadata={"source": "f.txt"})]

        result = engine.build_knowledge_base("/fake/dir")
        assert result["documents_count"] == 1
        assert result["chunks_count"] == 1
        assert "processing_time_ms" in result
        assert engine.is_ready is True

    @patch("app.services.rag.engine.DocumentParser")
    def test_build_no_documents(self, mock_parser):
        engine = RAGEngine()
        mock_parser.parse_directory.return_value = []
        with pytest.raises(ValueError, match="未找到文档"):
            engine.build_knowledge_base("/empty/dir")


class TestQuery:
    @pytest.fixture
    def engine(self):
        engine = RAGEngine()
        engine._ready = True
        engine.search = MagicMock()
        engine.transformer = MagicMock()
        return engine

    def test_not_ready_raises_error(self):
        engine = RAGEngine()
        with pytest.raises(ValueError, match="知识库未加载"):
            engine.query("test question", llm_config=LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test"))

    def test_no_llm_config_raises_error(self, engine):
        with pytest.raises(ValueError, match="请提供 LLM 配置"):
            engine.query("test question", llm_config=None)

    @patch("app.services.rag.engine.LLMFactory")
    def test_basic_query(self, mock_factory, engine, sample_documents, mock_llm_response):
        engine.search.search.return_value = (sample_documents[:3], 100.0)

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response
        mock_factory.create.return_value = mock_llm

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        resp = engine.query("MBR膜通量？", llm_config=cfg, use_query_rewrite=False, use_multi_query=False)

        assert isinstance(resp, QueryResponse)
        assert "100 mg/L" in resp.answer
        assert len(resp.sources) == 3
        assert resp.retrieval_time_ms == 100.0
        assert resp.generation_time_ms is not None

    @patch("app.services.rag.engine.LLMFactory")
    def test_query_with_rewrite(self, mock_factory, engine, sample_documents, mock_llm_response):
        engine.search.search.return_value = (sample_documents[:2], 50.0)
        engine.transformer.rewrite_query.return_value = "MBR 膜生物反应器 膜通量 标准"
        engine.transformer.generate_multi_queries.return_value = []

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response
        mock_factory.create.return_value = mock_llm

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        resp = engine.query("MBR膜通量？", llm_config=cfg, use_query_rewrite=True)

        assert resp.query_rewrite == "MBR 膜生物反应器 膜通量 标准"
        engine.transformer.rewrite_query.assert_called_once()

    @patch("app.services.rag.engine.LLMFactory")
    def test_query_with_multi_query(self, mock_factory, engine, sample_documents, mock_llm_response):
        # 主查询和多查询分别返回不同的结果
        main_docs = [sample_documents[0]]
        extra1_docs = [sample_documents[1]]
        extra2_docs = [sample_documents[2]]
        engine.search.search.side_effect = [
            (main_docs, 30.0),
            (extra1_docs, 10.0),
            (extra2_docs, 10.0),
        ]
        engine.transformer.rewrite_query.return_value = None
        engine.transformer.generate_multi_queries.return_value = ["MBR 膜通量参数", "膜生物反应器标准"]

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response
        mock_factory.create.return_value = mock_llm

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        resp = engine.query("MBR膜通量？", llm_config=cfg, use_query_rewrite=False, use_multi_query=True)

        assert resp.multi_queries == ["MBR 膜通量参数", "膜生物反应器标准"]
        # 每个多查询都是不同的文档，最终 sources 应有 3 个
        assert len(resp.sources) == 3
        assert engine.search.search.call_count == 3

    @patch("app.services.rag.engine.LLMFactory")
    def test_multi_query_dedup(self, mock_factory, engine, sample_documents, mock_llm_response):
        """验证多查询检索的去重逻辑"""
        # 所有查询（主 + 子查询）都返回相同文档
        engine.search.search.return_value = ([sample_documents[0]], 10.0)
        engine.transformer.rewrite_query.return_value = None
        engine.transformer.generate_multi_queries.return_value = ["mq1", "mq2"]

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response
        mock_factory.create.return_value = mock_llm

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        resp = engine.query("test", llm_config=cfg, use_query_rewrite=False, use_multi_query=True)

        assert len(resp.sources) == 1

    def test_env_prompt_structure(self):
        """验证领域提示词的结构"""
        assert "{context}" in ENV_PROMPT
        assert "{question}" in ENV_PROMPT
        assert "资深环境工程专家" in ENV_PROMPT
        assert "参考资料" in ENV_PROMPT


class TestStreamQuery:
    @pytest.fixture
    def engine(self):
        engine = RAGEngine()
        engine._ready = True
        engine.search = MagicMock()
        return engine

    def test_not_ready_yields_error(self):
        engine = RAGEngine()
        chunks = list(engine.stream_query("test", llm_config=LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")))
        assert len(chunks) == 1
        assert "error" in chunks[0]

    def test_no_llm_config_yields_error(self, engine):
        chunks = list(engine.stream_query("test", llm_config=None))
        assert len(chunks) == 1
        assert "error" in chunks[0]

    @patch("app.services.rag.engine.LLMFactory")
    def test_streaming_tokens(self, mock_factory, engine, sample_documents, mock_llm_stream):
        engine.search.search.return_value = (sample_documents[:2], 50.0)

        mock_llm = MagicMock()
        mock_llm.stream.return_value = mock_llm_stream
        mock_factory.create.return_value = mock_llm

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        chunks = list(engine.stream_query("test", llm_config=cfg))

        tokens = [c for c in chunks if "token" in c]
        assert len(tokens) >= 3

        final = chunks[-1]
        assert "sources" in final
        assert final["done"] is True
