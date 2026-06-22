export const API_BASE_URL = 'http://localhost:8000/api/v1';

export const APP_NAME = '环境工程 RAG Ultimate';

// 与 backend app/models/schemas.py LLMProvider 一致
export const PROVIDERS = [
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'qwen', label: '通义千问 (Qwen)' },
  { value: 'glm', label: '智谱 GLM' },
  { value: 'kimi', label: 'Kimi (月之暗面)' },
] as const;

export const DEFAULT_QUERY_OPTIONS = {
  queryRewrite: true,
  multiQuery: false,
  useReranker: true,
  topK: 5,
};

export const SUPPORTED_UPLOAD_FORMATS = [
  '.pdf',
  '.txt',
  '.md',
  '.docx',
  '.csv',
  '.json',
];

export const NAV_ITEMS = [
  { page: 'chat' as const, label: '对话', icon: '💬' },
  { page: 'knowledge' as const, label: '知识库管理', icon: '📚' },
  { page: 'evaluation' as const, label: '评估', icon: '📊' },
  { page: 'status' as const, label: '系统状态', icon: '⚙️' },
] as const;
