import React from 'react';
import type { NavPage } from '../types';
import Sidebar from './Sidebar';
import ChatPanel from './ChatPanel';
import KnowledgeBase from './KnowledgeBase';
import Evaluation from './Evaluation';
import SystemStatus from './SystemStatus';
import type { ChatMessage, QueryOptions as QueryOptionsType } from '../types';

interface LayoutProps {
  currentPage: NavPage;
  onPageChange: (page: NavPage) => void;
  // Chat
  messages: ChatMessage[];
  isStreaming: boolean;
  onSend: (query: string) => void;
  onStop: () => void;
  onClear: () => void;
  // Model
  provider: string;
  model: string;
  onProviderChange: (p: string) => void;
  onModelChange: (m: string) => void;
  // Options
  queryOptions: QueryOptionsType;
}

const Layout: React.FC<LayoutProps> = ({
  currentPage,
  onPageChange,
  messages,
  isStreaming,
  onSend,
  onStop,
  onClear,
  provider,
  model,
  onProviderChange,
  onModelChange,
  queryOptions,
}) => {
  const renderContent = () => {
    switch (currentPage) {
      case 'chat':
        return (
          <ChatPanel
            messages={messages}
            isStreaming={isStreaming}
            onSend={onSend}
            onStop={onStop}
            onClear={onClear}
            provider={provider}
            model={model}
            onProviderChange={onProviderChange}
            onModelChange={onModelChange}
            queryOptions={queryOptions}
          />
        );
      case 'knowledge':
        return <KnowledgeBase />;
      case 'evaluation':
        return <Evaluation />;
      case 'status':
        return <SystemStatus />;
      default:
        return null;
    }
  };

  return (
    <div style={styles.container}>
      <Sidebar
        currentPage={currentPage}
        onPageChange={onPageChange}
        currentModel={model}
        currentProvider={provider}
      />
      <main style={styles.main}>{renderContent()}</main>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    height: '100vh',
    width: '100vw',
    overflow: 'hidden',
  },
  main: {
    flex: 1,
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
};

export default Layout;
