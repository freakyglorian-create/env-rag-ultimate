/* ====== 与 backend app/models/schemas.py 对齐 ====== */

export interface ModelInfo {
  provider: string;
  model: string;
  description: string;
}

export interface QueryRequest {
  question: string;
  top_k?: number;
  provider: string;
  model?: string;
  api_key: string;
  use_reranker?: boolean;
  use_query_rewrite?: boolean;
  use_multi_query?: boolean;
}

export interface SourceDocument {
  content: string;
  source: string;
  page?: number;
  score?: number;
  chunk_id?: string;
}

export interface QueryResponse {
  answer: string;
  sources: SourceDocument[];
  retrieval_time_ms?: number;
  generation_time_ms?: number;
  total_time_ms?: number;
  provider_used: string;
  model_used: string;
  query_rewrite?: string;
  multi_queries?: string[];
}

/* ====== System Status ====== */
export interface SystemStatus {
  status: string;
  version: string;
  knowledge_base_loaded: boolean;
  embedding_model: string;
  reranker_enabled: boolean;
  query_rewrite_enabled: boolean;
  multi_query_enabled: boolean;
  available_models: ModelInfo[];
}

/* ====== Chat ====== */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceDocument[];
  metadata?: {
    retrieval_time_ms?: number;
    generation_time_ms?: number;
    total_time_ms?: number;
    model?: string;
    provider?: string;
    query_rewrite?: string;
    multi_queries?: string[];
  };
  timestamp: number;
  isStreaming?: boolean;
}

/* ====== KB ====== */
export interface KBDocument {
  name: string;
  size: number;
}

/* ====== Evaluation ====== */
export interface EvalRequest {
  provider: string;
  model?: string;
  api_key: string;
}

/* ====== Nav ====== */
export type NavPage = 'chat' | 'knowledge' | 'evaluation' | 'status';

/* ====== Query Options ====== */
export interface QueryOptions {
  queryRewrite: boolean;
  multiQuery: boolean;
  useReranker: boolean;
  topK: number;
}

/* ====== Key Verification ====== */
export interface VerifyKeyRequest {
  provider: string;
  api_key: string;
}

export interface VerifyKeyResponse {
  valid: boolean;
  models: string[];
  message: string;
}
