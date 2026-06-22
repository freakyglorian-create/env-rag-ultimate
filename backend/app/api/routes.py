"""
FastAPI 路由 - 支持 LLM Factory 模式
API Key 由前端用户传入，不再从 .env 读取
"""
import shutil, json, os
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import settings, KNOWLEDGE_DIR, UPLOAD_DIR
from app.models.schemas import *
from app.services.rag.engine import get_rag_engine
from app.services.llm.factory import LLMFactory
from app.services.evaluation.evaluator import get_evaluator
from app.services.parser.document_parser import DocumentParser

router = APIRouter()


@router.get("/status", response_model=SystemStatus)
def status():
    engine = get_rag_engine()
    models = [ModelInfo(**m) for m in LLMFactory.get_provider_catalog()]
    return SystemStatus(
        status="running", version=settings.APP_VERSION,
        knowledge_base_loaded=engine.is_ready,
        embedding_model=settings.EMBEDDING_MODEL,
        reranker_enabled=settings.USE_RERANKER,
        query_rewrite_enabled=settings.ENABLE_QUERY_REWRITE,
        multi_query_enabled=settings.ENABLE_MULTI_QUERY,
        available_models=models,
    )


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    try:
        engine = get_rag_engine()
        llm_config = LLMConfig(provider=req.provider, model=req.model, api_key=req.api_key)
        return engine.query(
            question=req.question, top_k=req.top_k,
            llm_config=llm_config,
            use_reranker=req.use_reranker,
            use_query_rewrite=req.use_query_rewrite,
            use_multi_query=req.use_multi_query,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/query/stream")
def query_stream(req: QueryRequest):
    async def gen():
        try:
            engine = get_rag_engine()
            if not engine.is_ready:
                yield f"data: {json.dumps({'error': '知识库未加载'})}\n\n"; return
            llm_config = LLMConfig(provider=req.provider, model=req.model, api_key=req.api_key)
            for chunk in engine.stream_query(
                question=req.question, top_k=req.top_k,
                llm_config=llm_config,
                use_reranker=req.use_reranker,
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/upload", response_model=UploadResponse)
def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "文件名不能为空")
    ext = Path(file.filename).suffix.lower()
    if ext not in DocumentParser.SUPPORTED:
        raise HTTPException(400, f"不支持 {ext}")
    path = UPLOAD_DIR / file.filename
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return UploadResponse(success=True, filename=file.filename, size=path.stat().st_size, file_type=ext)


@router.post("/kb/build", response_model=BuildKBResponse)
def build_kb():
    try:
        engine = get_rag_engine()
        r = engine.build_knowledge_base(str(KNOWLEDGE_DIR))
        return BuildKBResponse(success=True, message=f"构建成功: {r['chunks_count']} 块", **r)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/kb/load")
def load_kb():
    try:
        if get_rag_engine().load_knowledge_base():
            return {"success": True}
        raise HTTPException(404, "知识库不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/kb/documents")
def list_docs():
    return [{"name": f.name, "size": f.stat().st_size} for f in KNOWLEDGE_DIR.rglob("*") if f.is_file()]


@router.get("/models", response_model=List[ModelInfo])
def list_models():
    """返回静态模型目录，可用性取决于用户提供的 API Key"""
    return [ModelInfo(**m) for m in LLMFactory.get_provider_catalog()]


@router.post("/models/verify", response_model=VerifyKeyResponse)
def verify_api_key(req: VerifyKeyRequest):
    """验证用户 API Key 是否有效，并返回该提供商的可用模型列表"""
    llm_config = LLMConfig(provider=req.provider, api_key=req.api_key)
    valid = LLMFactory.verify_key(llm_config)
    if valid:
        models = LLMFactory.get_models_for_provider(req.provider)
        return VerifyKeyResponse(valid=True, models=models, message="API Key 有效")
    return VerifyKeyResponse(valid=False, models=[], message="API Key 无效或已过期")


@router.post("/evaluation/run")
def run_eval(req: EvalRequest):
    try:
        llm_config = LLMConfig(provider=req.provider, model=req.model, api_key=req.api_key)
        report = get_evaluator().run_evaluation(llm_config=llm_config)
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/evaluation/report")
def get_report():
    return get_evaluator().get_latest_report()
