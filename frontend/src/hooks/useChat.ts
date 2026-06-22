import { useState, useCallback, useRef } from 'react';
import type { ChatMessage, QueryOptions as QueryOptionsType, SourceDocument } from '../types';
import { streamQuery } from '../api/client';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    (query: string, options: QueryOptionsType, provider: string, model: string, apiKey: string) => {
      if (!query.trim() || isStreaming) return;
      if (!apiKey.trim()) return;

      const userMsg: ChatMessage = {
        id: generateId(),
        role: 'user',
        content: query.trim(),
        timestamp: Date.now(),
      };

      const assistantMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: '',
        sources: [],
        metadata: {},
        timestamp: Date.now(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      const assistantId = assistantMsg.id;
      let sourcesBuffer: SourceDocument[] = [];

      const controller = streamQuery(
        {
          question: query.trim(),
          provider,
          model,
          api_key: apiKey,
          use_query_rewrite: options.queryRewrite,
          use_multi_query: options.multiQuery,
          use_reranker: options.useReranker,
          top_k: options.topK,
        },
        // onToken
        (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + token } : m,
            ),
          );
        },
        // onSources
        (sources) => {
          sourcesBuffer = sources;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, sources: sources } : m,
            ),
          );
        },
        // onDone
        () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, isStreaming: false, sources: sourcesBuffer.length > 0 ? sourcesBuffer : m.sources }
                : m,
            ),
          );
          setIsStreaming(false);
          abortRef.current = null;
        },
        // onError
        (errorMsg) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content || `错误: ${errorMsg}`, isStreaming: false }
                : m,
            ),
          );
          setIsStreaming(false);
          abortRef.current = null;
        },
      );

      abortRef.current = controller;
    },
    [isStreaming],
  );

  const stopStreaming = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setIsStreaming(false);
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m)),
    );
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, isStreaming, sendMessage, stopStreaming, clearMessages };
}
