/* ====== 系统状态 ====== */
export interface SystemStatus {
  version: string;
  knowledge_base: KBStatus;
  embedding_model: string;
  reranker_status: string;
  ollama_status: 'running' | 'stopped' | 'unknown';
  models: ModelInfo[];
}

export interface KBStatus {
  loaded: boolean;
  document_count: number;
  chunk_count: number;
  last_built?: string;
}

export interface ModelInfo {
  provider: string;
  model: string;
  available: boolean;
  is_local: boolean;
}

/* ====== 查询 ====== */
export interface QueryRequest {
  query: string;
  provider?: string;
  model?: string;
  query_rewrite?: boolean;
  multi_query?: boolean;
  use_reranker?: boolean;
  top_k?: number;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  retrieval_time: number;
  generation_time: number;
  total_time: number;
  model: string;
  provider: string;
  query_rewrite?: string;
  multi_queries?: string[];
}

export interface Source {
  content: string;
  score: number;
  metadata: Record<string, string>;
}

/* ====== SSE 流式 ====== */
export interface SSEChunk {
  type: 'token' | 'sources' | 'metadata' | 'done' | 'error';
  content?: string;
  sources?: Source[];
  metadata?: {
    retrieval_time?: number;
    generation_time?: number;
    model?: string;
    provider?: string;
    query_rewrite?: string;
    multi_queries?: string[];
  };
  error?: string;
}

/* ====== 聊天消息 ====== */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  metadata?: {
    retrieval_time?: number;
    generation_time?: number;
    total_time?: number;
    model?: string;
    provider?: string;
    query_rewrite?: string;
    multi_queries?: string[];
  };
  timestamp: number;
  isStreaming?: boolean;
}

/* ====== 知识库 ====== */
export interface KBDocument {
  filename: string;
  filepath: string;
  size: number;
  uploaded_at: string;
  chunks?: number;
}

export interface KBBuildRequest {
  chunk_size?: number;
  chunk_overlap?: number;
}

export interface KBLoadRequest {
  persist_directory?: string;
}

/* ====== 评估 ====== */
export interface EvaluationRequest {
  questions?: string[];
  provider?: string;
  model?: string;
}

export interface EvaluationResult {
  question: string;
  answer: string;
  scores: {
    relevance: number;
    faithfulness: number;
    completeness: number;
    clarity: number;
  };
  total_score: number;
  sources?: Source[];
}

export interface EvaluationReport {
  results: EvaluationResult[];
  average_scores: {
    relevance: number;
    faithfulness: number;
    completeness: number;
    clarity: number;
    total: number;
  };
  timestamp: string;
  model: string;
  provider: string;
}

/* ====== 导航 ====== */
export type NavPage = 'chat' | 'knowledge' | 'evaluation' | 'status';

/* ====== 查询选项 ====== */
export interface QueryOptions {
  queryRewrite: boolean;
  multiQuery: boolean;
  useReranker: boolean;
  topK: number;
}
