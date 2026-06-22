# ============================================
# 环境工程 RAG Ultimate - Dockerfile
# ============================================
FROM python:3.11-slim

LABEL maintainer="env-rag-ultimate"
LABEL description="环境工程 RAG 知识库问答系统"

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 先复制 requirements.txt 以利用 Docker 缓存层
COPY backend/requirements.txt ./requirements.txt

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 复制知识库数据
COPY data/ ./data/

# 创建必要的目录
RUN mkdir -p /app/data/vector_store /app/data/uploads /app/data/evaluation

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/status || exit 1

# 启动命令
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
