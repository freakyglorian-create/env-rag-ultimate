"""
LLM Factory - 静态工厂模式，根据用户请求创建 ChatOpenAI 实例
所有提供商均使用 OpenAI 兼容 API
API Key 由前端用户传入，不存储在服务端
"""
from typing import Dict, List, Optional, Iterator

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

from app.models.schemas import LLMConfig, LLMProvider


# ===== 静态提供商目录（不含 API Key）=====
PROVIDER_CATALOG: Dict[str, dict] = {
    LLMProvider.DEEPSEEK: {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "description": "DeepSeek 大模型",
    },
    LLMProvider.QWEN: {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-turbo",
        "models": ["qwen-turbo", "qwen-plus", "qwen-max"],
        "description": "通义千问 (Qwen)",
    },
    LLMProvider.GLM: {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
        "models": ["glm-4", "glm-4-flash", "glm-4-plus"],
        "description": "智谱 GLM",
    },
    LLMProvider.KIMI: {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "description": "Kimi (月之暗面)",
    },
}


class LLMFactory:
    """
    LLM 工厂 - 纯静态方法，每次请求创建新实例
    不做缓存（API Key 每次不同），无需单例
    """

    @staticmethod
    def create(config: LLMConfig, temperature: float = 0.3, streaming: bool = False) -> ChatOpenAI:
        """
        根据 LLMConfig 创建 ChatOpenAI 实例

        Args:
            config: 包含 provider、model、api_key 的配置对象
            temperature: 生成温度
            streaming: 是否启用流式输出

        Returns:
            ChatOpenAI 实例

        Raises:
            ValueError: 不支持的提供商
        """
        provider_key = config.provider if isinstance(config.provider, str) else config.provider.value
        catalog = PROVIDER_CATALOG.get(config.provider)
        if catalog is None:
            raise ValueError(f"不支持的 LLM 提供商: {config.provider}")

        model = config.model or catalog["default_model"]
        base_url = catalog["base_url"]

        return ChatOpenAI(
            model=model,
            api_key=config.api_key,
            base_url=base_url,
            temperature=temperature,
            streaming=streaming,
            max_tokens=4096,
            request_timeout=60,
        )

    @staticmethod
    def get_provider_catalog() -> List[dict]:
        """
        返回静态模型目录，供 /models 端点使用

        Returns:
            列表，每项包含 provider、model、description
        """
        result = []
        for provider, catalog in PROVIDER_CATALOG.items():
            provider_value = provider.value if hasattr(provider, "value") else provider
            for model in catalog["models"]:
                result.append({
                    "provider": provider_value,
                    "model": model,
                    "description": catalog["description"],
                })
        return result

    @staticmethod
    def get_models_for_provider(provider: LLMProvider) -> List[str]:
        """
        返回指定提供商的模型列表

        Args:
            provider: LLM 提供商枚举值

        Returns:
            模型名称列表
        """
        catalog = PROVIDER_CATALOG.get(provider)
        if not catalog:
            return []
        return catalog["models"]

    @staticmethod
    def verify_key(config: LLMConfig) -> bool:
        """
        通过调用 /models 接口验证 API Key 是否有效

        Args:
            config: 包含 provider 和 api_key 的配置对象

        Returns:
            True 表示 Key 有效，False 表示无效或请求失败
        """
        catalog = PROVIDER_CATALOG.get(config.provider)
        if not catalog:
            return False
        try:
            import httpx
            resp = httpx.get(
                f"{catalog['base_url']}/models",
                headers={"Authorization": f"Bearer {config.api_key}"},
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False
