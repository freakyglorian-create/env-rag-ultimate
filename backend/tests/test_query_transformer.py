"""
Query Transformer 测试
"""
import pytest
from unittest.mock import patch, MagicMock

from app.models.schemas import LLMConfig, LLMProvider
from app.services.query_transform.transformer import (
    QueryTransformer, QUERY_REWRITE_PROMPT, MULTI_QUERY_PROMPT,
)


class TestQueryTransformerInit:
    def test_create_instance(self):
        qt = QueryTransformer()
        assert qt is not None


class TestRewriteQuery:
    @pytest.fixture
    def transformer(self):
        return QueryTransformer()

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_no_llm_config_returns_none(self, mock_llm, transformer):
        result = transformer.rewrite_query("MBR膜通量是多少？", llm_config=None)
        assert result is None

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_rewrite_disabled_by_config(self, mock_llm, transformer, monkeypatch):
        monkeypatch.setattr("app.services.query_transform.transformer.settings.ENABLE_QUERY_REWRITE", False)
        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        result = transformer.rewrite_query("测试问题", llm_config=cfg)
        assert result is None

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_successful_rewrite(self, mock_chat_cls, transformer, monkeypatch):
        monkeypatch.setattr("app.services.query_transform.transformer.settings.ENABLE_QUERY_REWRITE", True)
        mock_instance = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = "MBR 膜生物反应器 膜通量 标准范围"
        mock_instance.invoke.return_value = mock_resp
        mock_chat_cls.return_value = mock_instance

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        result = transformer.rewrite_query("MBR膜通量是多少？", llm_config=cfg)
        assert result == "MBR 膜生物反应器 膜通量 标准范围"

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_rewrite_identical_to_input(self, mock_chat_cls, transformer):
        """改写结果与原问题相同时返回 None"""
        mock_instance = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = "MBR膜通量是多少？"
        mock_instance.invoke.return_value = mock_resp
        mock_chat_cls.return_value = mock_instance

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        result = transformer.rewrite_query("MBR膜通量是多少？", llm_config=cfg)
        assert result is None

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_rewrite_empty_response(self, mock_chat_cls, transformer):
        mock_instance = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = "   "
        mock_instance.invoke.return_value = mock_resp
        mock_chat_cls.return_value = mock_instance

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        result = transformer.rewrite_query("test", llm_config=cfg)
        assert result is None

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_llm_error_returns_none(self, mock_chat_cls, transformer):
        mock_chat_cls.side_effect = Exception("LLM API Error")

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        result = transformer.rewrite_query("test question", llm_config=cfg)
        assert result is None

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_response_without_content_attr(self, mock_chat_cls, transformer):
        """响应对象没有 .content 属性，回退到 str()"""
        mock_instance = MagicMock()
        mock_resp = "改写后的查询字符串"
        mock_instance.invoke.return_value = mock_resp
        mock_chat_cls.return_value = mock_instance

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        result = transformer.rewrite_query("原始问题", llm_config=cfg)
        assert result == "改写后的查询字符串"


class TestGenerateMultiQueries:
    @pytest.fixture
    def transformer(self):
        return QueryTransformer()

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_no_llm_config_returns_empty(self, mock_llm, transformer):
        result = transformer.generate_multi_queries("test", llm_config=None)
        assert result == []

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_disabled_by_config(self, mock_llm, transformer, monkeypatch):
        monkeypatch.setattr("app.services.query_transform.transformer.settings.ENABLE_MULTI_QUERY", False)
        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        result = transformer.generate_multi_queries("test", llm_config=cfg)
        assert result == []

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_successful_generation(self, mock_chat_cls, transformer, monkeypatch):
        monkeypatch.setattr("app.services.query_transform.transformer.settings.ENABLE_MULTI_QUERY", True)
        mock_instance = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = "MBR 膜通量 参数\n膜生物反应器 设计标准\nMBR工艺 运行参数"
        mock_instance.invoke.return_value = mock_resp
        mock_chat_cls.return_value = mock_instance

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        result = transformer.generate_multi_queries("MBR膜通量", n=3, llm_config=cfg)
        assert len(result) == 3
        assert "MBR" in result[0]

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_respects_n_limit(self, mock_chat_cls, transformer, monkeypatch):
        monkeypatch.setattr("app.services.query_transform.transformer.settings.ENABLE_MULTI_QUERY", True)
        """验证返回结果不超过 n 个"""
        mock_instance = MagicMock()
        mock_resp = MagicMock()
        # LLM 返回 5 行，但 n=2 应该截断
        lines = [f"query variant {i}" for i in range(5)]
        mock_resp.content = "\n".join(lines)
        mock_instance.invoke.return_value = mock_resp
        mock_chat_cls.return_value = mock_instance

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        result = transformer.generate_multi_queries("test", n=2, llm_config=cfg)
        assert len(result) == 2

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_llm_error_returns_empty(self, mock_chat_cls, transformer):
        mock_chat_cls.side_effect = Exception("LLM Error")

        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        result = transformer.generate_multi_queries("test", llm_config=cfg)
        assert result == []


class TestPrompts:
    def test_rewrite_prompt_formatting(self):
        prompt = QUERY_REWRITE_PROMPT.format(question="什么是MBR？")
        assert "MBR" in prompt
        assert "改写查询" in prompt

    def test_multi_query_prompt_formatting(self):
        prompt = MULTI_QUERY_PROMPT.format(question="SCR脱硝", n=3)
        assert "SCR脱硝" in prompt
        assert "3" in prompt
