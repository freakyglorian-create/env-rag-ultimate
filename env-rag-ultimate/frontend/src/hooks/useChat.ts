import { useState, useCallback, useRef } from 'react';
import type { ChatMessage, QueryOptions as QueryOptionsType } from '../types';
import { streamQuery } from '../api/client';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    (query: string, options: QueryOptionsType, provider: string, model: string) => {
      if (!query.trim() || isStreaming) return;

      // Add user message
      const userMsg: ChatMessage = {
        id: generateId(),
        role: 'user',
        content: query.trim(),
        timestamp: Date.now(),
      };

      // Add placeholder assistant message
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

      // Start SSE stream
      const controller = streamQuery(
        {
          query: query.trim(),
          provider,
          model,
          query_rewrite: options.queryRewrite,
          multi_query: options.multiQuery,
          use_reranker: options.useReranker,
          top_k: options.topK,
        },
        // onChunk
        (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + token }
                : m,
            ),
          );
        },
        // onSources
        (sources) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, sources } : m,
            ),
          );
        },
        // onMetadata
        (metadata) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    metadata: {
                      retrieval_time: metadata.retrieval_time,
                      generation_time: metadata.generation_time,
                      total_time: metadata.total_time,
                      model: metadata.model,
                      provider: metadata.provider,
                      query_rewrite: metadata.query_rewrite,
                      multi_queries: metadata.multi_queries,
                    },
                  }
                : m,
            ),
          );
        },
        // onDone
        () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, isStreaming: false } : m,
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
                ? { ...m, content: `Error: ${errorMsg}`, isStreaming: false }
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
