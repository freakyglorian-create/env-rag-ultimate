import axios from 'axios';
import type {
  SystemStatus,
  QueryRequest,
  QueryResponse,
  ModelInfo,
  KBDocument,
  KBBuildRequest,
  KBLoadRequest,
  EvaluationRequest,
  EvaluationReport,
} from '../types';
import { API_BASE_URL } from '../utils/constants';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/* ====== 系统状态 ====== */
export async function getSystemStatus(): Promise<SystemStatus> {
  const { data } = await api.get<SystemStatus>('/status');
  return data;
}

/* ====== 查询 ====== */
export async function postQuery(req: QueryRequest): Promise<QueryResponse> {
  const { data } = await api.post<QueryResponse>('/query', req);
  return data;
}

/* ====== SSE 流式查询 ====== */
export function streamQuery(
  req: QueryRequest,
  onChunk: (chunk: string) => void,
  onSources: (sources: QueryResponse['sources']) => void,
  onMetadata: (metadata: QueryResponse) => void,
  onDone: () => void,
  onError: (error: string) => void,
): AbortController {
  const controller = new AbortController();

  fetch(`${API_BASE_URL}/query/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6).trim();
            if (jsonStr === '[DONE]') {
              onDone();
              return;
            }
            try {
              const parsed = JSON.parse(jsonStr);
              if (parsed.type === 'token' && parsed.content) {
                onChunk(parsed.content);
              } else if (parsed.type === 'sources' && parsed.sources) {
                onSources(parsed.sources);
              } else if (parsed.type === 'metadata' && parsed.metadata) {
                onMetadata(parsed.metadata);
              } else if (parsed.type === 'error') {
                onError(parsed.error || 'Unknown error');
                return;
              } else if (parsed.type === 'done') {
                onDone();
                return;
              }
            } catch {
              // ignore non-JSON lines
            }
          }
        }
      }
      onDone();
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(err.message);
      }
    });

  return controller;
}

/* ====== 模型 ====== */
export async function getModels(): Promise<ModelInfo[]> {
  const { data } = await api.get<ModelInfo[]>('/models');
  return data;
}

/* ====== 知识库 ====== */
export async function buildKnowledgeBase(req?: KBBuildRequest): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/kb/build', req || {});
  return data;
}

export async function loadKnowledgeBase(req?: KBLoadRequest): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/kb/load', req || {});
  return data;
}

export async function getDocuments(): Promise<KBDocument[]> {
  const { data } = await api.get<KBDocument[]>('/kb/documents');
  return data;
}

export async function uploadDocument(file: File): Promise<{ message: string; filename: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post<{ message: string; filename: string }>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  });
  return data;
}

/* ====== 评估 ====== */
export async function runEvaluation(req?: EvaluationRequest): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/evaluation/run', req || {});
  return data;
}

export async function getEvaluationReport(): Promise<EvaluationReport> {
  const { data } = await api.get<EvaluationReport>('/evaluation/report');
  return data;
}

export default api;
