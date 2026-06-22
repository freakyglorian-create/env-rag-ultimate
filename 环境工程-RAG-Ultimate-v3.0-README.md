# 环境工程 RAG Ultimate v3.0.0

企业级智能问答系统 — Hybrid Search + Reranking + Query Transform + LLM Factory + RAGAS 评估

`FastAPI` `React + TypeScript` `LangChain` `FAISS` `BGE Embedding` `Docker`

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Node](https://img.shields.io/badge/Node-18+-green) ![License](https://img.shields.io/badge/License-MIT-purple) ![RAG](https://img.shields.io/badge/RAG-Advanced-orange)

---

## 目录

- [项目概览](#项目概览)
- [系统架构](#系统架构)
- [核心特性](#核心特性)
- [多模型工厂](#多模型工厂)
- [API 文档](#api-文档)
- [快速开始](#快速开始)
- [评估体系](#评估体系)
- [项目结构](#项目结构)
- [路线图](#路线图)

---

## 项目概览

一个面向**环境工程垂直领域**的企业级 RAG 智能问答系统。采用 Hybrid Search（稠密+稀疏混合检索）、Cross-Encoder Reranking（重排序）、Query Transform（查询变换）等 Advanced RAG 技术，实现高精度、可评估的领域知识问答。

### 核心能力

| 能力 | 说明 |
|------|------|
| **Hybrid Search** | FAISS 稠密检索 + BM25 稀疏检索，RRF 倒数秩融合 |
| **Cross-Encoder Reranker** | BGE-Reranker 精排，Top-50 召回 → Top-5 精排 |
| **Query Transform** | 查询改写 + 多查询生成，提升召回覆盖率 |
| **LLM Factory** | 工厂模式，4 家国产模型按请求动态创建 |
| **RAGAS 评估** | 忠实度 / 相关性 / 精确率 / 召回率 |
| **Docker 部署** | 前后端分离，一键 Docker Compose 部署 |

> **设计理念：** 用户在前端自选模型 + 自填 API Key，后端通过 LLM Factory 工厂模式按请求创建 LLM 实例。不硬编码任何 API Key，支持 DeepSeek / Qwen / GLM / Kimi 四家国产大模型无缝切换。

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端 (React + TypeScript)                     │
│  Chat Panel  │  Model Selector  │  Query Options  │  Eval Panel │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                      后端 (FastAPI)                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    REST API /api/v1                        │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  服务层                                                    │  │
│  │  ┌──────────┐ ┌────────────┐ ┌───────────┐ ┌───────────┐ │  │
│  │  │  LLM     │ │  Query     │ │  Hybrid   │ │  Reranker │ │  │
│  │  │  Factory │ │  Transform │ │  Search   │ │           │ │  │
│  │  └──────────┘ └────────────┘ └───────────┘ └───────────┘ │  │
│  │  ┌──────────┐ ┌────────────┐                              │  │
│  │  │ RAG      │ │ Evaluator  │                              │  │
│  │  │ Engine   │ │            │                              │  │
│  │  └──────────┘ └────────────┘                              │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  存储层:  FAISS │ BM25 │ Documents                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    LLM 供应商                                    │
│     DeepSeek    │    Qwen    │    GLM    │    Kimi              │
└─────────────────────────────────────────────────────────────────┘
```

### RAG 检索管道

```
用户 Query → Query Transform → Hybrid Search → RRF Fusion → Cross-Encoder Reranker → LLM Generation → Answer + Sources

  ┌─ Dense Retrieval (FAISS + BGE) ─┐
  │                                  ├──→ RRF Fusion (k=60) ──→ Top-50 ──→ BGE-Reranker ──→ Top-5 ──→ LLM
  └─ Sparse Retrieval (BM25 + jieba)┘
```

### LLM Factory 工厂模式

```
前端请求 (provider + apiKey + model)
    │
    ▼
LLMFactory.create()
    │
    ▼
PROVIDER_CATALOG
    ├── DeepSeek Config  ──→ ChatOpenAI ──→ DeepSeek API
    ├── Qwen Config      ──→ ChatOpenAI ──→ Qwen API
    ├── GLM Config       ──→ ChatOpenAI ──→ GLM API
    └── Kimi Config      ──→ ChatOpenAI ──→ Kimi API
```

### 请求生命周期

```
用户 → 前端 → FastAPI → RAG Engine
                           ├──→ Query Transform ──→ LLM Factory ──→ LLM API (查询改写)
                           ├──→ Hybrid Search (检索)
                           └──→ LLM Factory ──→ LLM API (生成答案)
                           ←── QueryResponse ←──
       ←── JSON Response ←──
用户 ←── 显示答案 + 来源
```

---

## 核心特性

### Hybrid Search（混合检索）

采用 **Dense + Sparse 双路检索 + RRF 融合**的工业级检索架构：

| 检索路径 | 技术 | 优势 | 权重 |
|----------|------|------|------|
| Dense（稠密） | FAISS + BAAI/bge-large-zh-v1.5 | 语义理解强，能召回同义词/近义词 | 0.7 |
| Sparse（稀疏） | BM25 + jieba 中文分词 | 精确匹配强，专有名词/缩写/数字 | 0.3 |
| 融合 | RRF（Reciprocal Rank Fusion） | 综合两种检索优势 | k=60 |

**RRF 公式：** `score(d) = sum(1 / (k + rank_i(d)))`，k 通常取 60。

### Cross-Encoder Reranking（重排序）

**两阶段检索架构：**

- **Stage 1 — 召回：** Hybrid Search 召回 Top-50 候选文档
- **Stage 2 — 精排：** BGE-Reranker-base（Cross-Encoder）对 Query-Document 对进行细粒度交互打分，取 Top-5 送入 LLM

Bi-Encoder（Embedding）将 Query 和 Doc 分别编码，速度快但交互弱；Cross-Encoder 将两者拼接后一起编码，精度高但计算量大。两阶段架构用轻量方法召回候选集，再用精排模型选出最优。

### Query Transform（查询变换）

在检索前对用户查询进行改写和扩展：

- **Query Rewriting（查询改写）：** 用 LLM（temperature=0.1）将口语化查询改写为标准表达，如 "污水怎么处理" → "城市污水处理工艺及排放标准"
- **Multi-Query（多查询生成）：** 从一个查询生成 3 个不同角度的子问题（temperature=0.5），分别检索后合并结果，提升召回覆盖率

### 多格式文档解析

| 格式 | 解析库 | 说明 |
|------|--------|------|
| .txt | 多编码自动检测 | UTF-8 / GBK / GB2312 |
| .md | markdown 库 | 保留标题层级 |
| .pdf | pypdf | 逐页提取文本 |
| .docx | python-docx | 段落级提取 |
| .html | BeautifulSoup4 | 去除标签，保留正文 |
| .xlsx | openpyxl | 逐行读取 |

分块策略：`RecursiveCharacterTextSplitter`，chunk_size=512，chunk_overlap=100。

---

## 多模型工厂

### 设计理念

采用**工厂模式（Factory Pattern）**，每次请求根据用户提供的 `LLMConfig`（provider + api_key + model）创建新的 `ChatOpenAI` 实例：

- **不做缓存：** API Key 每请求不同，ChatOpenAI 仅是配置对象，创建开销极小
- **纯静态方法：** 无需单例，无需模块级实例
- **统一接口：** 所有供应商均通过 OpenAI 兼容接口调用，屏蔽差异
- **Key 验证：** 通过 `/models` 接口轻量验证 API Key 有效性

### 支持的模型

| 供应商 | Base URL | 模型 | 说明 |
|--------|----------|------|------|
| **DeepSeek** | `https://api.deepseek.com/v1` | deepseek-chat, deepseek-reasoner | 高性价比推理 |
| **Qwen (通义千问)** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | qwen-turbo, qwen-plus, qwen-max | 阿里云大模型 |
| **GLM (智谱)** | `https://open.bigmodel.cn/api/paas/v4` | glm-4, glm-4-flash, glm-4-plus | GLM-4-Flash 永久免费 |
| **Kimi (月之暗面)** | `https://api.moonshot.cn/v1` | moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k | 超长上下文 |

### 使用方式

```json
POST /api/v1/query
{
  "question": "COD 排放标准是多少？",
  "provider": "deepseek",
  "model": "deepseek-chat",
  "api_key": "sk-your-own-key",
  "use_reranker": true,
  "use_query_rewrite": true
}
```

后端处理：

```python
llm_config = LLMConfig(provider=req.provider, model=req.model, api_key=req.api_key)
llm = LLMFactory.create(llm_config, temperature=0.3)
```

> ⚠️ **安全设计：** 后端不硬编码任何 API Key。Key 由前端用户输入，通过请求体传递，后端仅用于创建当次 LLM 实例，不做持久化存储。

---

## API 文档

所有接口前缀：`/api/v1`

| 方法 | 端点 | 说明 | 请求体 |
|------|------|------|--------|
| GET | `/status` | 系统状态 | - |
| GET | `/models` | 获取模型目录 | - |
| POST | `/models/verify` | 验证 API Key | VerifyKeyRequest |
| POST | `/query` | 查询问答 | QueryRequest |
| POST | `/query/stream` | 流式查询 (SSE) | QueryRequest |
| POST | `/upload` | 上传文档 | FormData(file) |
| POST | `/kb/build` | 构建知识库 | - |
| POST | `/kb/load` | 加载知识库 | - |
| GET | `/kb/documents` | 列出文档 | - |
| POST | `/evaluation/run` | 运行评估 | VerifyKeyRequest |
| GET | `/evaluation/report` | 获取评估报告 | - |

### 核心数据模型

```python
# QueryRequest — 查询请求
class QueryRequest(BaseModel):
    question: str           # 问题（1-2000 字符）
    top_k: int = 5          # 召回文档数（1-20）
    provider: LLMProvider   # 模型供应商（deepseek/qwen/glm/kimi）
    model: Optional[str]    # 模型名称（可选，默认使用供应商默认模型）
    api_key: str            # API Key（必填）
    use_reranker: bool      # 是否启用重排序
    use_query_rewrite: bool # 是否启用查询改写
    use_multi_query: bool   # 是否启用多查询生成

# LLMConfig — 内部 LLM 配置
class LLMConfig(BaseModel):
    provider: LLMProvider
    model: Optional[str] = None
    api_key: str
```

### API Key 验证

```json
POST /api/v1/models/verify
{
  "provider": "deepseek",
  "api_key": "sk-your-key"
}
```

响应：

```json
{
  "valid": true,
  "models": ["deepseek-chat", "deepseek-reasoner"],
  "message": "API Key 有效"
}
```

---

## 快速开始

### 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 推荐 3.11 |
| Node.js | 18+ | 前端构建 |
| Git | 最新 | 代码管理 |
| LLM API Key | - | DeepSeek / Qwen / GLM / Kimi 任选其一 |

### 一键部署

1. **克隆项目**

   ```bash
   git clone https://github.com/your-username/env-rag-ultimate.git
   cd env-rag-ultimate
   ```

2. **创建 Python 虚拟环境**

   ```bash
   cd backend
   python -m venv venv
   # Windows PowerShell
   .\venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

3. **安装依赖**

   ```bash
   # 国内用户使用清华镜像加速
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

4. **启动后端**

   ```bash
   python main.py
   # 或
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

   看到 `[Startup] 知识库加载成功` 即表示启动成功。

5. **启动前端**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   访问 `http://localhost:5173`，在前端界面选择模型、填写 API Key 即可开始问答。

### Docker 部署

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f backend

# 停止
docker-compose down
```

> ✅ **Docker 部署注意：** 使用 Docker 时，前端通过 Nginx 反向代理访问后端 API，访问 `http://localhost` 即可。

### HuggingFace 离线模式

如果 Embedding/Reranker 模型已下载到本地缓存，可设置离线模式避免重复下载：

```bash
# Windows PowerShell
$env:HF_HUB_OFFLINE = "1"

# macOS / Linux
export HF_HUB_OFFLINE=1
```

---

## 评估体系

### RAGAS 四大指标

```
用户问题 ──┐
检索上下文 ─┤──→ Faithfulness（忠实度）── 答案是否基于上下文
生成答案 ──┤──→ Answer Relevancy（答案相关性）── 答案是否回答问题
参考答案 ──┘──→ Context Precision（上下文精确率）── 检索是否精准
              Context Recall（上下文召回率）── 检索是否全面
```

| 指标 | 含义 | 计算方式 | 范围 |
|------|------|----------|------|
| **Faithfulness** | 答案是否忠实于检索上下文 | 答案中的声明有多少能在上下文中找到依据 | 0-1 |
| **Answer Relevancy** | 答案是否回答了问题 | 基于答案反向生成问题，计算与原问题的相似度 | 0-1 |
| **Context Precision** | 检索结果中有多少是相关的 | 相关 chunk 数 / 总检索 chunk 数 | 0-1 |
| **Context Recall** | 相关文档是否被全部召回 | 被覆盖的参考信息 / 总参考信息 | 0-1 |

### 黄金测试集

内置 12 条环境工程领域问答对，覆盖 6 个子领域：

| 子领域 | 示例问题 |
|--------|----------|
| **水污染控制** | MBR 膜通量、COD 排放标准 |
| **大气污染控制** | SCR 脱硝温度、袋式除尘风速 |
| **环境影响评价** | 环评审批时限、公众参与公示 |
| **固体废物处理** | 焚烧二噁英限值、危废温度 |
| **环境法规标准** | PM2.5 二级标准 |
| **碳排放管理** | 原煤碳排放因子、碳市场行业 |

### 运行评估

```json
POST /api/v1/evaluation/run
{
  "provider": "deepseek",
  "api_key": "sk-your-key"
}

GET /api/v1/evaluation/report
```

---

## 项目结构

```
env-rag-ultimate/
├── backend/                          # 后端服务
│   ├── main.py                       # FastAPI 入口
│   ├── requirements.txt              # Python 依赖
│   ├── .env.example                  # 环境变量模板
│   └── app/
│       ├── api/routes.py             # REST API 路由
│       ├── core/config.py            # Pydantic Settings 配置
│       ├── models/schemas.py         # 数据模型（LLMProvider/LLMConfig/QueryRequest）
│       └── services/
│           ├── llm/factory.py        # LLM 工厂（DeepSeek/Qwen/GLM/Kimi）
│           ├── rag/
│           │   ├── engine.py         # RAG 核心引擎
│           │   └── hybrid_search.py  # Hybrid Search 混合检索
│           ├── query_transform/
│           │   └── transformer.py     # 查询改写 / 多查询生成
│           ├── evaluation/
│           │   └── evaluator.py      # RAGAS 自动化评估
│           ├── embedding/engine.py   # BGE Embedding 引擎
│           └── parser/
│               └── document_parser.py # 多格式文档解析
├── frontend/                         # 前端应用
│   ├── src/
│   │   ├── components/               # React 组件
│   │   │   ├── ChatPanel.tsx         # 聊天面板
│   │   │   ├── ModelSelector.tsx     # 模型选择器
│   │   │   ├── QueryOptions.tsx      # 查询选项
│   │   │   ├── Evaluation.tsx        # 评估面板
│   │   │   └── SourceCard.tsx        # 来源卡片
│   │   ├── api/client.ts             # API 客户端
│   │   ├── hooks/useChat.ts          # 聊天 Hook
│   │   └── types/index.ts            # TypeScript 类型
│   └── package.json
├── data/
│   └── knowledge_base/               # 6 篇环境工程知识文档
│       ├── 01_水污染控制.txt
│       ├── 02_大气污染控制.txt
│       ├── 03_环境影响评价.txt
│       ├── 04_固体废物处理.txt
│       ├── 05_环境法规标准.txt
│       └── 06_碳排放管理.txt
├── scripts/
│   ├── setup.sh                      # 一键安装
│   ├── start.sh                      # 一键启动
│   └── build_kb.py                   # 知识库构建
├── Dockerfile                        # Docker 镜像
├── docker-compose.yml                # Docker Compose 编排
└── nginx.conf                        # Nginx 反向代理
```

---

## 路线图

```
v3.0 (当前)                 v3.1 (计划中)                v3.2 (规划中)
LLM Factory 4 家国产模型      Agentic RAG (ReAct)          多模态支持
API Key 前端配置              对话历史管理                  知识库增量更新
Key 验证接口                  引用高亮                      用户反馈闭环 (RLHF)
    │                            │                            │
    └────────── 演进 ────────────┴────────── 演进 ────────────┘
```

| 版本 | 特性 | 状态 |
|------|------|------|
| v1.0 | 基础 RAG（向量检索 + 单模型） | ✅ 已完成 |
| v2.0 | Hybrid Search + Reranker + 多模型 Gateway | ✅ 已完成 |
| v3.0 | LLM Factory 工厂模式 + 前端自选模型 + API Key 验证 | 🔵 当前版本 |
| v3.1 | Agentic RAG（ReAct）+ 对话历史 + 引用高亮 | 🟠 计划中 |
| v3.2 | 多模态解析 + 增量更新 + 用户反馈闭环 | 🟣 规划中 |

---

*环境工程 RAG Ultimate v3.0.0 | Advanced RAG 智能问答系统*

*Hybrid Search + Reranking + Query Transform + LLM Factory + RAGAS Evaluation*
