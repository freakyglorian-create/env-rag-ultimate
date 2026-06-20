# ============================================
# 环境工程 RAG Ultimate - 一键安装脚本
# ============================================
#!/usr/bin/env bash
set -e

echo "============================================"
echo "  环境工程 RAG Ultimate - 环境安装脚本"
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

# ----- 1. 检测 Python 版本 -----
echo ">>> [1/5] 检测 Python 版本..."
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    error "未找到 Python，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

info "当前 Python 版本: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    error "Python 版本过低，需要 3.10 或更高版本"
    exit 1
fi

# ----- 2. 创建虚拟环境 -----
echo ""
echo ">>> [2/5] 创建 Python 虚拟环境..."
VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    warn "虚拟环境已存在 ($VENV_DIR/)，跳过创建"
else
    $PYTHON_CMD -m venv "$VENV_DIR"
    info "虚拟环境创建成功: $VENV_DIR/"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"
info "虚拟环境已激活"

# ----- 3. 安装 Python 依赖 -----
echo ""
echo ">>> [3/5] 安装 Python 依赖..."
if [ -f "backend/requirements.txt" ]; then
    pip install --upgrade pip -q
    pip install -r backend/requirements.txt
    info "Python 依赖安装完成"
else
    error "未找到 backend/requirements.txt"
    exit 1
fi

# ----- 4. 安装 jieba 分词数据 -----
echo ""
echo ">>> [4/5] 安装 jieba 分词数据..."
$PYTHON_CMD -c "
import jieba
print('jieba 初始化完成，分词数据已就绪')
" 2>/dev/null
if [ $? -eq 0 ]; then
    info "jieba 分词数据安装完成"
else
    warn "jieba 分词数据安装失败，首次使用时会自动下载"
fi

# ----- 5. 提示安装 Ollama -----
echo ""
echo ">>> [5/5] 检查 Ollama..."
if command -v ollama &>/dev/null; then
    info "Ollama 已安装"
    OLLAMA_STATUS=$(curl -s http://localhost:11434/api/tags 2>/dev/null | $PYTHON_CMD -c "import sys,json; print('running' if json.load(sys.stdin) else 'stopped')" 2>/dev/null || echo "not running")
    if [ "$OLLAMA_STATUS" = "running" ]; then
        info "Ollama 服务正在运行"
    else
        warn "Ollama 服务未运行，请执行: ollama serve"
    fi
else
    warn "未检测到 Ollama，请手动安装以使用本地 LLM"
    echo ""
    echo "  安装方式:"
    echo "    curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    echo "  安装后拉取推荐模型:"
    echo "    ollama pull qwen2.5:7b"
fi

# ----- 完成 -----
echo ""
echo "============================================"
echo "  安装完成！"
echo "============================================"
echo ""
echo "  后续步骤:"
echo "    1. 确保 Ollama 已安装并运行: ollama serve"
echo "    2. 构建知识库:           python scripts/build_kb.py"
echo "    3. 启动服务:             bash scripts/start.sh"
echo ""
