import { useState, useCallback } from 'react';
import type { QueryOptions as QueryOptionsType } from '../types';
import { DEFAULT_QUERY_OPTIONS } from '../utils/constants';

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async <T>(fn: () => Promise<T>): Promise<T | null> => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      return result;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(msg);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, setError, execute };
}

export function useQueryOptions() {
  const [options, setOptions] = useState<QueryOptionsType>(DEFAULT_QUERY_OPTIONS);

  const toggleRewrite = useCallback(() => {
    setOptions((prev) => ({ ...prev, queryRewrite: !prev.queryRewrite }));
  }, []);

  const toggleMultiQuery = useCallback(() => {
    setOptions((prev) => ({ ...prev, multiQuery: !prev.multiQuery }));
  }, []);

  const toggleReranker = useCallback(() => {
    setOptions((prev) => ({ ...prev, useReranker: !prev.useReranker }));
  }, []);

  const setTopK = useCallback((topK: number) => {
    setOptions((prev) => ({ ...prev, topK }));
  }, []);

  return { options, toggleRewrite, toggleMultiQuery, toggleReranker, setTopK };
}
