"""
环境工程 RAG Ultimate - FastAPI 入口文件
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings, VECTOR_STORE_PATH
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时自动加载知识库"""
    # 启动时尝试自动加载已有的知识库
    print("[Startup] 正在检查知识库...")
    try:
        from app.services.rag.engine import get_rag_engine
        engine = get_rag_engine()
        if engine.load_knowledge_base():
            print("[Startup] 知识库加载成功")
        else:
            print("[Startup] 未找到已有知识库，请通过 /api/v1/kb/build 构建或 /api/v1/kb/load 加载")
    except Exception as e:
        print(f"[Startup] 知识库加载失败: {e}")

    yield

    # 关闭时清理资源
    print("[Shutdown] 应用关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
