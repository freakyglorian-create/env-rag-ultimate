"""
环境工程 RAG Ultimate - 知识库构建脚本

用法:
    python scripts/build_kb.py
    python scripts/build_kb.py --dir data/knowledge_base
    python scripts/build_kb.py --rebuild
"""
import sys
import os
import argparse
import time

# 将项目根目录和 backend 目录加入 Python 路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.config import settings, KNOWLEDGE_DIR
from app.services.rag.engine import get_rag_engine


def build_knowledge_base(directory: str, rebuild: bool = False):
    """构建知识库"""
    print("=" * 50)
    print("  环境工程 RAG Ultimate - 知识库构建")
    print("=" * 50)
    print()

    # 检查目录是否存在
    if not os.path.isdir(directory):
        print(f"[错误] 知识库目录不存在: {directory}")
        sys.exit(1)

    # 列出目录中的文件
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if not files:
        print(f"[错误] 知识库目录为空: {directory}")
        sys.exit(1)

    print(f"[信息] 知识库目录: {directory}")
    print(f"[信息] 发现文件数: {len(files)}")
    for f in files:
        size = os.path.getsize(os.path.join(directory, f))
        print(f"       - {f} ({size:,} bytes)")
    print()

    # 获取 RAG 引擎
    engine = get_rag_engine()

    # 如果不是重建，先尝试加载已有索引
    if not rebuild:
        print("[信息] 尝试加载已有知识库...")
        if engine.load_knowledge_base():
            print("[信息] 已有知识库加载成功，如需重建请使用 --rebuild 参数")
            print()
            return
        print("[信息] 未找到已有知识库，开始构建...")
    else:
        print("[信息] 强制重建模式，跳过加载...")

    print()

    # 构建知识库
    print("[构建] 开始构建知识库，首次运行需要下载 Embedding 模型，请耐心等待...")
    print()

    t0 = time.time()
    try:
        result = engine.build_knowledge_base(directory)
        elapsed = time.time() - t0
    except ValueError as e:
        print(f"[错误] 构建失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[错误] 构建过程出现异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 打印结果
    print()
    print("=" * 50)
    print("  构建完成！")
    print("=" * 50)
    print(f"  文档数量:   {result['documents_count']}")
    print(f"  文本块数量: {result['chunks_count']}")
    print(f"  构建耗时:   {result['time_ms']:.0f} ms ({elapsed:.1f} s)")
    print(f"  存储路径:   {settings.VECTOR_STORE_PATH / 'env_kb'}")
    print()
    print("  现在可以启动服务进行查询了:")
    print("    bash scripts/start.sh")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="构建环境工程 RAG 知识库")
    parser.add_argument(
        "--dir", "-d",
        type=str,
        default=str(KNOWLEDGE_DIR),
        help=f"知识库文档目录 (默认: {KNOWLEDGE_DIR})"
    )
    parser.add_argument(
        "--rebuild", "-r",
        action="store_true",
        help="强制重建知识库（忽略已有索引）"
    )
    args = parser.parse_args()

    build_knowledge_base(directory=args.dir, rebuild=args.rebuild)
