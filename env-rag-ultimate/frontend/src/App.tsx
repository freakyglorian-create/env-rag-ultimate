import React, { useState, createContext, useContext, useMemo } from 'react';
import type { NavPage, QueryOptions as QueryOptionsType } from './types';
import { useChat } from './hooks/useChat';
import { useQueryOptions } from './hooks/useApi';
import Layout from './components/Layout';

// App-level context
interface AppContextType {
  provider: string;
  model: string;
  onProviderChange: (p: string) => void;
  onModelChange: (m: string) => void;
  queryOptions: QueryOptionsType;
  toggleRewrite: () => void;
  toggleMultiQuery: () => void;
  toggleReranker: () => void;
  setTopK: (k: number) => void;
}

export const AppContext = createContext<AppContextType>({} as AppContextType);

export const useAppContext = () => useContext(AppContext);

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<NavPage>('chat');
  const [provider, setProvider] = useState('ollama');
  const [model, setModel] = useState('qwen2.5:7b');

  const {
    options: queryOptions,
    toggleRewrite,
    toggleMultiQuery,
    toggleReranker,
    setTopK,
  } = useQueryOptions();

  const { messages, isStreaming, sendMessage, stopStreaming, clearMessages } = useChat();

  const handleSend = (query: string) => {
    sendMessage(query, queryOptions, provider, model);
  };

  const contextValue = useMemo(
    () => ({
      provider,
      model,
      onProviderChange: setProvider,
      onModelChange: setModel,
      queryOptions,
      toggleRewrite,
      toggleMultiQuery,
      toggleReranker,
      setTopK,
    }),
    [provider, model, queryOptions, toggleRewrite, toggleMultiQuery, toggleReranker, setTopK],
  );

  return (
    <AppContext.Provider value={contextValue}>
      <Layout
        currentPage={currentPage}
        onPageChange={setCurrentPage}
        messages={messages}
        isStreaming={isStreaming}
        onSend={handleSend}
        onStop={stopStreaming}
        onClear={clearMessages}
        provider={provider}
        model={model}
        onProviderChange={setProvider}
        onModelChange={setModel}
        queryOptions={queryOptions}
      />
    </AppContext.Provider>
  );
};

export default App;
