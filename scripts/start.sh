# ============================================
# 环境工程 RAG Ultimate - 启动脚本
# ============================================
#!/usr/bin/env bash
set -e

echo "============================================"
echo "  环境工程 RAG Ultimate - 启动脚本"
echo "============================================"
echo ""

# ----- 颜色定义 -----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# ----- 激活虚拟环境 -----
VENV_DIR="$PROJECT_ROOT/backend/venv"
if [ -d "$VENV_DIR/bin" ]; then
    source "$VENV_DIR/bin/activate"
    info "虚拟环境已激活"
elif [ -d "$VENV_DIR/Scripts" ]; then
    # Windows Git Bash 兼容
    source "$VENV_DIR/Scripts/activate"
    info "虚拟环境已激活"
else
    warn "未找到虚拟环境，使用系统 Python"
fi

# ----- 启动后端 -----
echo ""
echo ">>> 启动后端服务 (FastAPI)..."
BACKEND_PORT=8000

# 检查端口是否被占用
if lsof -i :"$BACKEND_PORT" &>/dev/null; then
    warn "端口 $BACKEND_PORT 已被占用，尝试终止旧进程..."
    lsof -t -i :"$BACKEND_PORT" | xargs kill -9 2>/dev/null || true
    sleep 1
fi

cd "$PROJECT_ROOT/backend"
uvicorn main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload &
BACKEND_PID=$!
info "后端 PID: $BACKEND_PID"

# ----- 等待后端就绪 -----
echo ""
echo ">>> 等待后端服务就绪..."
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s "http://localhost:$BACKEND_PORT/api/v1/status" &>/dev/null; then
        info "后端服务已就绪 (http://localhost:$BACKEND_PORT)"
        break
    fi
    sleep 1
    WAITED=$((WAITED + 1))
    if [ $((WAITED % 5)) -eq 0 ]; then
        warn "已等待 ${WAITED}s..."
    fi
done

if [ $WAITED -ge $MAX_WAIT ]; then
    error "后端服务启动超时 (${MAX_WAIT}s)"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# ----- 启动前端 -----
echo ""
echo ">>> 启动前端开发服务器 (Vite)..."
cd "$PROJECT_ROOT/frontend"

if [ -d "node_modules" ]; then
    info "node_modules 已存在，跳过安装"
else
    info "安装前端依赖..."
    npm install
fi

npx vite --host 0.0.0.0 &
FRONTEND_PID=$!
info "前端 PID: $FRONTEND_PID"

# ----- 完成 -----
echo ""
echo "============================================"
echo "  所有服务已启动！"
echo "============================================"
echo ""
echo "  后端 API:  http://localhost:$BACKEND_PORT"
echo "  前端页面: http://localhost:5173"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "============================================"
echo ""

# ----- 信号处理 -----
cleanup() {
    echo ""
    info "正在停止服务..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    info "所有服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 保持脚本运行
wait
