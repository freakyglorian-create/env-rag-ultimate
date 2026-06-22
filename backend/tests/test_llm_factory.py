"""
LLM Factory 测试
"""
import pytest
from unittest.mock import patch, MagicMock

from app.models.schemas import LLMConfig, LLMProvider
from app.services.llm.factory import LLMFactory, PROVIDER_CATALOG


class TestProviderCatalog:
    def test_all_providers_registered(self):
        assert LLMProvider.DEEPSEEK in PROVIDER_CATALOG
        assert LLMProvider.QWEN in PROVIDER_CATALOG
        assert LLMProvider.GLM in PROVIDER_CATALOG
        assert LLMProvider.KIMI in PROVIDER_CATALOG

    def test_deepseek_catalog(self):
        cat = PROVIDER_CATALOG[LLMProvider.DEEPSEEK]
        assert "api.deepseek.com" in cat["base_url"]
        assert cat["default_model"] == "deepseek-chat"
        assert "deepseek-chat" in cat["models"]
        assert "deepseek-reasoner" in cat["models"]

    def test_qwen_catalog(self):
        cat = PROVIDER_CATALOG[LLMProvider.QWEN]
        assert "dashscope.aliyuncs.com" in cat["base_url"]
        assert "qwen-turbo" in cat["models"]

    def test_glm_catalog(self):
        cat = PROVIDER_CATALOG[LLMProvider.GLM]
        assert "bigmodel.cn" in cat["base_url"]
        assert "glm-4" in cat["models"]

    def test_kimi_catalog(self):
        cat = PROVIDER_CATALOG[LLMProvider.KIMI]
        assert "moonshot.cn" in cat["base_url"]
        assert "moonshot-v1-8k" in cat["models"]


class TestLLMFactoryCreate:
    @patch("app.services.llm.factory.ChatOpenAI")
    def test_create_with_default_model(self, mock_chat_openai, llm_config_deepseek):
        LLMFactory.create(llm_config_deepseek)
        mock_chat_openai.assert_called_once()
        kwargs = mock_chat_openai.call_args[1]
        assert kwargs["model"] == "deepseek-chat"
        assert kwargs["api_key"] == "sk-test-ds-key"
        assert "api.deepseek.com" in kwargs["base_url"]
        assert kwargs["temperature"] == 0.3
        assert kwargs["streaming"] is False
        assert kwargs["max_tokens"] == 4096

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_create_with_custom_model(self, mock_chat_openai, llm_config_with_model):
        LLMFactory.create(llm_config_with_model)
        kwargs = mock_chat_openai.call_args[1]
        assert kwargs["model"] == "deepseek-reasoner"

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_create_with_streaming(self, mock_chat_openai, llm_config_deepseek):
        LLMFactory.create(llm_config_deepseek, streaming=True)
        kwargs = mock_chat_openai.call_args[1]
        assert kwargs["streaming"] is True

    @patch("app.services.llm.factory.ChatOpenAI")
    def test_create_with_temperature(self, mock_chat_openai, llm_config_deepseek):
        LLMFactory.create(llm_config_deepseek, temperature=0.8)
        kwargs = mock_chat_openai.call_args[1]
        assert kwargs["temperature"] == 0.8

    def test_create_unsupported_provider(self):
        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        # 绕过类型检查模拟不支持的 provider
        cfg.provider = "unsupported"  # type: ignore
        with pytest.raises(ValueError, match="不支持的 LLM 提供商"):
            LLMFactory.create(cfg)


class TestGetProviderCatalog:
    def test_returns_all_models(self):
        catalog = LLMFactory.get_provider_catalog()
        assert isinstance(catalog, list)
        assert len(catalog) > 0
        # 每个条目有 provider / model / description
        for item in catalog:
            assert "provider" in item
            assert "model" in item
            assert "description" in item

    def test_contains_deepseek_models(self):
        catalog = LLMFactory.get_provider_catalog()
        providers = {item["provider"] for item in catalog}
        assert "deepseek" in providers

    def test_all_four_providers_present(self):
        catalog = LLMFactory.get_provider_catalog()
        providers = {item["provider"] for item in catalog}
        assert providers == {"deepseek", "qwen", "glm", "kimi"}


class TestGetModelsForProvider:
    def test_valid_provider(self):
        models = LLMFactory.get_models_for_provider(LLMProvider.DEEPSEEK)
        assert "deepseek-chat" in models
        assert "deepseek-reasoner" in models

    def test_custom_provider(self):
        """使用不在 catalog 中的 provider"""
        # 模拟一个不存在的 provider
        class FakeProvider:
            value = "nonexistent"
        # 用真实枚举值但构造一个不在 catalog 的 key
        from enum import Enum

        models = LLMFactory.get_models_for_provider(None)  # type: ignore
        assert models == []


class TestVerifyKey:
    @patch("httpx.get")
    def test_valid_key(self, mock_get, llm_config_deepseek):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        assert LLMFactory.verify_key(llm_config_deepseek) is True
        mock_get.assert_called_once()
        args = mock_get.call_args
        assert "/models" in args[0][0]
        assert args[1]["headers"]["Authorization"] == "Bearer sk-test-ds-key"

    @patch("httpx.get")
    def test_invalid_key(self, mock_get, llm_config_deepseek):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        assert LLMFactory.verify_key(llm_config_deepseek) is False

    @patch("httpx.get")
    def test_network_error(self, mock_get, llm_config_deepseek):
        mock_get.side_effect = Exception("Connection refused")
        assert LLMFactory.verify_key(llm_config_deepseek) is False

    def test_unknown_provider(self):
        cfg = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test")
        cfg.provider = "unknown"  # type: ignore
        assert LLMFactory.verify_key(cfg) is False
