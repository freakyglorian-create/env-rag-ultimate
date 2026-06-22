import axios from 'axios';
import type {
  SystemStatus,
  QueryRequest,
  QueryResponse,
  ModelInfo,
  KBDocument,
  VerifyKeyRequest,
  VerifyKeyResponse,
  SourceDocument,
} from '../types';
import { API_BASE_URL } from '../utils/constants';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/* ====== System ====== */
export async function getSystemStatus(): Promise<SystemStatus> {
  const { data } = await api.get<SystemStatus>('/status');
  return data;
}

/* ====== Query ====== */
export async function postQuery(req: QueryRequest): Promise<QueryResponse> {
  const { data } = await api.post<QueryResponse>('/query', req);
  return data;
}

/* ====== SSE Stream ====== */
export function streamQuery(
  req: QueryRequest,
  onToken: (token: string) => void,
  onSources: (sources: SourceDocument[]) => void,
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
        throw new Error(`HTTP ${response.status}`);
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
            if (!jsonStr) continue;
            try {
              const parsed = JSON.parse(jsonStr);
              // Backend sends: {token: "..."} or {sources: [...], done: true} or {error: "..."}
              if (parsed.error) {
                onError(parsed.error);
                return;
              }
              if (parsed.token) {
                onToken(parsed.token);
              }
              if (parsed.sources) {
                onSources(parsed.sources);
              }
              if (parsed.done) {
                onDone();
                return;
              }
            } catch {
              // ignore malformed JSON
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

/* ====== Models ====== */
export async function getModels(): Promise<ModelInfo[]> {
  const { data } = await api.get<ModelInfo[]>('/models');
  return data;
}

export async function verifyApiKey(req: VerifyKeyRequest): Promise<VerifyKeyResponse> {
  const { data } = await api.post<VerifyKeyResponse>('/models/verify', req);
  return data;
}

/* ====== KB ====== */
export async function buildKnowledgeBase(): Promise<{ success: boolean; message: string; chunks_count: number }> {
  const { data } = await api.post('/kb/build');
  return data;
}

export async function loadKnowledgeBase(): Promise<{ success: boolean }> {
  const { data } = await api.post('/kb/load');
  return data;
}

export async function getDocuments(): Promise<KBDocument[]> {
  const { data } = await api.get<KBDocument[]>('/kb/documents');
  return data;
}

export async function uploadDocument(file: File): Promise<{ success: boolean; filename: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  });
  return data;
}

/* ====== Evaluation ====== */
export async function runEvaluation(req: { provider: string; model?: string; api_key: string }) {
  const { data } = await api.post('/evaluation/run', req, { timeout: 300000 });
  return data;
}

export async function getEvaluationReport() {
  const { data } = await api.get('/evaluation/report');
  return data;
}

export default api;
