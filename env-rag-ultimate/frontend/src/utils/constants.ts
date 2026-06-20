export const API_BASE_URL = 'http://localhost:8000/api/v1';

export const APP_NAME = '环境工程 RAG Ultimate';

export const PROVIDERS = [
  { value: 'ollama', label: 'Ollama' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'siliconflow', label: 'SiliconFlow' },
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
