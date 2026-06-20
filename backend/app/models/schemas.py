"""
Pydantic 数据模型
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    SILICONFLOW = "siliconflow"
    OLLAMA = "ollama"


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    provider: Optional[LLMProvider] = None
    model: Optional[str] = None
    use_reranker: bool = Field(default=True)
    use_query_rewrite: bool = Field(default=True)
    use_multi_query: bool = Field(default=False)


class SourceDocument(BaseModel):
    content: str
    source: str
    page: int = 1
    score: Optional[float] = None
    chunk_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    retrieval_time_ms: Optional[float] = None
    generation_time_ms: Optional[float] = None
    total_time_ms: Optional[float] = None
    provider_used: str = ""
    model_used: str = ""
    query_rewrite: Optional[str] = None
    multi_queries: Optional[List[str]] = None


class BuildKBResponse(BaseModel):
    success: bool
    message: str
    chunks_count: int
    documents_count: int
    processing_time_ms: float


class UploadResponse(BaseModel):
    success: bool
    filename: str
    size: int
    file_type: str


class EvaluationReport(BaseModel):
    total_questions: int
    average_faithfulness: float
    average_relevancy: float
    average_precision: float
    average_recall: float
    overall_score: float
    per_question: List[Dict[str, Any]]
    generated_at: str


class ModelInfo(BaseModel):
    provider: str
    model: str
    description: str
    available: bool
    is_local: bool = False


class SystemStatus(BaseModel):
    status: str
    version: str
    knowledge_base_loaded: bool
    embedding_model: str
    reranker_enabled: bool
    query_rewrite_enabled: bool
    multi_query_enabled: bool
    available_models: List[ModelInfo]
    ollama_status: Optional[str] = None
