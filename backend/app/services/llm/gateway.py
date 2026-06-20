"""
多模型 LLM 网关 - 支持 Ollama 本地模型 / OpenAI / DeepSeek / 硅基流动 无缝切换
无需 API Key 即可使用 Ollama 本地模型
"""
import os
from typing import Optional, Dict, Any, List, Iterator
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage

from app.core.config import settings


class LLMGateway:
    """
    多模型 LLM 网关
    - Ollama: 本地模型，无需 API Key，推荐 qwen2.5:7b
    - OpenAI: GPT-4o / GPT-4o-mini
    - DeepSeek: deepseek-chat / deepseek-reasoner
    - 硅基流动: Qwen2.5-72B / DeepSeek-V3 等
    """

    PROVIDER_CONFIGS = {
        "ollama": {
            "base_url": settings.OLLAMA_BASE_URL,
            "api_key": "ollama",  # Ollama 不需要真实 key
            "models": ["qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b", "qwen2.5:72b",
                         "deepseek-r1:7b", "llama3.1:8b", "gemma2:9b", "mistral:7b"],
            "description": "Ollama 本地模型（无需 API Key）",
            "is_local": True,
        },
        "openai": {
            "base_url": settings.OPENAI_BASE_URL,
            "api_key_env": "OPENAI_API_KEY",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "description": "OpenAI GPT 系列",
            "is_local": False,
        },
        "deepseek": {
            "base_url": settings.DEEPSEEK_BASE_URL,
            "api_key_env": "DEEPSEEK_API_KEY",
            "models": ["deepseek-chat", "deepseek-reasoner"],
            "description": "DeepSeek 大模型",
            "is_local": False,
        },
        "siliconflow": {
            "base_url": settings.SILICONFLOW_BASE_URL,
            "api_key_env": "SILICONFLOW_API_KEY",
            "models": ["Qwen/Qwen2.5-72B-Instruct", "Qwen/Qwen2.5-14B-Instruct",
                         "deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1"],
            "description": "硅基流动（开源模型聚合）",
            "is_local": False,
        },
    }

    def __init__(self):
        self._cache: Dict[str, ChatOpenAI] = {}
        self._ollama_available = None

    def _get_api_key(self, provider: str) -> Optional[str]:
        config = self.PROVIDER_CONFIGS.get(provider, {})
        if provider == "ollama":
            return "ollama"
        env_name = config.get("api_key_env")
        if env_name:
            return os.getenv(env_name)
        return None

    def is_ollama_running(self) -> bool:
        """检测 Ollama 服务是否在运行"""
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            import httpx
            resp = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3)
            self._ollama_available = resp.status_code == 200
        except Exception:
            self._ollama_available = False
        return self._ollama_available

    def get_ollama_models(self) -> List[str]:
        """获取 Ollama 已安装的模型列表"""
        try:
            import httpx
            resp = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def is_provider_available(self, provider: str) -> bool:
        if provider == "ollama":
            return self.is_ollama_running()
        key = self._get_api_key(provider)
        return key is not None and len(key) > 5

    def get_available_providers(self) -> List[Dict[str, Any]]:
        providers = []
        for provider, config in self.PROVIDER_CONFIGS.items():
            available = self.is_provider_available(provider)
            models = list(config["models"])

            # 对于 Ollama，显示实际已安装的模型
            if provider == "ollama" and available:
                installed = self.get_ollama_models()
                if installed:
                    models = installed

            for model in models:
                providers.append({
                    "provider": provider,
                    "model": model,
                    "description": config["description"],
                    "available": available,
                    "is_local": config.get("is_local", False),
                })
        return providers

    def get_llm(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        streaming: bool = False,
    ) -> ChatOpenAI:
        provider = provider or settings.DEFAULT_LLM_PROVIDER
        model = model or settings.DEFAULT_LLM_MODEL

        if not self.is_provider_available(provider):
            # 自动回退：ollama -> openai -> deepseek
            for fallback in ["ollama", "openai", "deepseek", "siliconflow"]:
                if self.is_provider_available(fallback):
                    provider = fallback
                    model = self.PROVIDER_CONFIGS[fallback]["models"][0]
                    break
            else:
                raise ValueError("没有可用的 LLM 提供商。请安装 Ollama 或配置 API Key。")

        cache_key = f"{provider}:{model}:{temperature}:{streaming}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        config = self.PROVIDER_CONFIGS[provider]
        llm = ChatOpenAI(
            model=model,
            api_key=self._get_api_key(provider),
            base_url=config["base_url"],
            temperature=temperature,
            streaming=streaming,
            max_tokens=4096,
        )
        self._cache[cache_key] = llm
        return llm

    def stream(self, messages: List[BaseMessage], provider=None, model=None, temperature=0.3) -> Iterator[str]:
        llm = self.get_llm(provider=provider, model=model, temperature=temperature, streaming=True)
        for chunk in llm.stream(messages):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            if content:
                yield content


_gateway: Optional[LLMGateway] = None


def get_llm_gateway() -> LLMGateway:
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway
