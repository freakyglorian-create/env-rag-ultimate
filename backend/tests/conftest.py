"""
共享测试夹具 & Mock 工具
"""
import sys
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 确保 backend 在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.models.schemas import LLMConfig, LLMProvider

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


# ===== 通用夹具 =====

@pytest.fixture
def sample_txt_path():
    return str(FIXTURES_DIR / "sample.txt")


@pytest.fixture
def sample_md_path():
    return str(FIXTURES_DIR / "sample.md")


@pytest.fixture
def sample_html_path():
    return str(FIXTURES_DIR / "sample.html")


@pytest.fixture
def sample_kb_dir():
    return str(FIXTURES_DIR)


# ===== LLM 相关夹具 =====

@pytest.fixture
def llm_config_deepseek():
    return LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="sk-test-ds-key")


@pytest.fixture
def llm_config_qwen():
    return LLMConfig(provider=LLMProvider.QWEN, api_key="sk-test-qwen-key")


@pytest.fixture
def llm_config_glm():
    return LLMConfig(provider=LLMProvider.GLM, api_key="test-glm-key")


@pytest.fixture
def llm_config_kimi():
    return LLMConfig(provider=LLMProvider.KIMI, api_key="sk-test-kimi-key")


@pytest.fixture
def llm_config_with_model():
    return LLMConfig(provider=LLMProvider.DEEPSEEK, model="deepseek-reasoner", api_key="sk-test-key")


# ===== Mock 夹具 =====

@pytest.fixture
def mock_chat_openai():
    """返回一个模拟的 ChatOpenAI 实例"""
    with patch("app.services.llm.factory.ChatOpenAI") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield instance


@pytest.fixture
def mock_llm_response():
    """模拟 LLM invoke 返回包含 .content 属性的对象"""
    resp = MagicMock()
    resp.content = "这是一个模拟的环境工程回答。根据GB 8978-1996标准，COD一级排放限值为100 mg/L。"
    return resp


@pytest.fixture
def mock_llm_stream():
    """模拟 LLM stream 返回的 token 块"""
    tokens = ["这是", "一个", "模拟的", "流式", "回答"]
    chunks = []
    for tok in tokens:
        chunk = MagicMock()
        chunk.content = tok
        chunks.append(chunk)
    return chunks


# ===== Document 夹具 =====

@pytest.fixture
def sample_documents():
    """返回一批模拟的 LangChain Document"""
    from langchain_core.documents import Document
    return [
        Document(
            page_content="MBR工艺的膜通量一般在15-30 L/(m²·h)之间，活性污泥浓度MLSS通常维持在8000-12000 mg/L。",
            metadata={"source": "01_水污染控制.txt", "page": 1, "type": "txt"},
        ),
        Document(
            page_content="SCR脱硝的反应温度窗口为300-400°C，脱硝效率可达80-95%。",
            metadata={"source": "02_大气污染控制.txt", "page": 1, "type": "txt"},
        ),
        Document(
            page_content="环评报告书的审批时限为60个工作日，自受理之日起计算。",
            metadata={"source": "03_环境影响评价.txt", "page": 1, "type": "txt"},
        ),
        Document(
            page_content="生活垃圾焚烧的二噁英排放限值为0.1 ng-TEQ/m³，烟气停留时间需满足2秒以上。",
            metadata={"source": "04_固体废物处理.txt", "page": 2, "type": "txt"},
        ),
        Document(
            page_content="PM2.5年均浓度的二级标准为35 μg/m³，一级标准为15 μg/m³。",
            metadata={"source": "05_环境法规标准.txt", "page": 1, "type": "txt"},
        ),
        Document(
            page_content="原煤的碳排放因子为1.9003 tCO2/t，无烟煤为2.53 tCO2/t。",
            metadata={"source": "06_碳排放管理.txt", "page": 1, "type": "txt"},
        ),
    ]


# ===== 评估相关夹具 =====

@pytest.fixture
def golden_set():
    return [
        {"question": "MBR工艺的膜通量一般是多少？", "ground_truth": "15-30 L/(m²·h)", "source": "01_水污染控制.txt", "category": "水污染控制"},
        {"question": "SCR脱硝的反应温度窗口是多少？", "ground_truth": "300-400°C", "source": "02_大气污染控制.txt", "category": "大气污染控制"},
    ]
