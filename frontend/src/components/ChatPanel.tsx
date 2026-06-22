import React, { useState, useRef, useEffect } from 'react';
import type { ChatMessage, QueryOptions as QueryOptionsType } from '../types';
import MessageBubble from './MessageBubble';
import ModelSelector from './ModelSelector';
import QueryOptionsPanel from './QueryOptions';

interface ChatPanelProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  onSend: (query: string) => void;
  onStop: () => void;
  onClear: () => void;
  provider: string;
  model: string;
  apiKey: string;
  onProviderChange: (p: string) => void;
  onModelChange: (m: string) => void;
  onApiKeyChange: (k: string) => void;
  queryOptions: QueryOptionsType;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  isStreaming,
  onSend,
  onStop,
  onClear,
  provider,
  model,
  apiKey,
  onProviderChange,
  onModelChange,
  onApiKeyChange,
  queryOptions,
}) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;
    onSend(input);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
  };

  return (
    <div style={styles.container}>
      {/* Top bar with model selector and options */}
      <div style={styles.topBar}>
        <div style={styles.topBarLeft}>
          <ModelSelector
            provider={provider}
            model={model}
            apiKey={apiKey}
            onProviderChange={onProviderChange}
            onModelChange={onModelChange}
            onApiKeyChange={onApiKeyChange}
          />
        </div>
        <div style={styles.topBarRight}>
          <QueryOptionsPanel />
        </div>
      </div>

      {/* Messages area */}
      <div style={styles.messagesArea}>
        {messages.length === 0 ? (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>🌍</div>
            <h2 style={styles.emptyTitle}>环境工程 RAG 问答系统</h2>
            <p style={styles.emptyDesc}>
              基于检索增强生成（RAG）的环境工程智能问答系统。
              <br />
              请在下方输入您的问题，例如：
            </p>
            <div style={styles.exampleList}>
              {[
                '什么是活性污泥法？',
                '污水处理中COD和BOD的区别是什么？',
                '大气污染的主要来源和控制方法有哪些？',
                '土壤修复的常见技术有哪些？',
              ].map((q, i) => (
                <div
                  key={i}
                  style={styles.exampleItem}
                  onClick={() => setInput(q)}
                >
                  {q}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div style={styles.messagesList}>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div style={styles.inputArea}>
        <div style={styles.inputContainer}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleTextareaInput}
            onKeyDown={handleKeyDown}
            placeholder="输入您的问题... (Enter 发送, Shift+Enter 换行)"
            style={styles.textarea}
            rows={1}
            disabled={isStreaming}
          />
          {isStreaming ? (
            <button onClick={onStop} style={styles.stopBtn} title="停止生成">
              <span style={styles.stopIcon}>■</span>
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              style={{
                ...styles.sendBtn,
                opacity: input.trim() ? 1 : 0.5,
                cursor: input.trim() ? 'pointer' : 'not-allowed',
              }}
              title="发送"
            >
              <span style={styles.sendIcon}>➤</span>
            </button>
          )}
        </div>
        <div style={styles.inputFooter}>
          <button onClick={onClear} style={styles.clearBtn}>
            清空对话
          </button>
          <span style={styles.hint}>
            {queryOptions.queryRewrite && '✓ Query Rewrite '}
            {queryOptions.multiQuery && '✓ Multi-Query '}
            {queryOptions.useReranker && '✓ Reranker '}
            Top-K: {queryOptions.topK}
          </span>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    overflow: 'hidden',
  },
  topBar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 20px',
    borderBottom: '1px solid var(--border-color)',
    background: 'var(--bg-secondary)',
    flexWrap: 'wrap',
    gap: '8px',
  },
  topBarLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  topBarRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  messagesArea: {
    flex: 1,
    overflow: 'hidden',
    position: 'relative',
  },
  messagesList: {
    height: '100%',
    overflowY: 'auto',
    padding: '20px 24px',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    padding: '40px',
    textAlign: 'center',
  },
  emptyIcon: {
    fontSize: '64px',
    marginBottom: '16px',
  },
  emptyTitle: {
    fontSize: '24px',
    fontWeight: 700,
    color: 'var(--text-primary)',
    marginBottom: '8px',
  },
  emptyDesc: {
    fontSize: '14px',
    color: 'var(--text-secondary)',
    marginBottom: '24px',
    lineHeight: 1.8,
  },
  exampleList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    maxWidth: '500px',
    width: '100%',
  },
  exampleItem: {
    padding: '10px 16px',
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border-color)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-secondary)',
    fontSize: '13px',
    cursor: 'pointer',
    transition: 'var(--transition)',
    textAlign: 'left',
  },
  inputArea: {
    padding: '12px 20px 16px',
    borderTop: '1px solid var(--border-color)',
    background: 'var(--bg-secondary)',
  },
  inputContainer: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '10px',
    background: 'var(--bg-primary)',
    border: '1px solid var(--border-color)',
    borderRadius: 'var(--radius-md)',
    padding: '8px 12px',
    transition: 'border-color 0.2s',
  },
  textarea: {
    flex: 1,
    background: 'transparent',
    border: 'none',
    outline: 'none',
    color: 'var(--text-primary)',
    fontSize: '14px',
    lineHeight: 1.5,
    resize: 'none',
    fontFamily: 'inherit',
    maxHeight: '200px',
  },
  sendBtn: {
    width: '36px',
    height: '36px',
    borderRadius: 'var(--radius-sm)',
    background: 'var(--accent-blue)',
    border: 'none',
    color: 'white',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    transition: 'var(--transition)',
  },
  sendIcon: {
    fontSize: '16px',
    lineHeight: 1,
  },
  stopBtn: {
    width: '36px',
    height: '36px',
    borderRadius: 'var(--radius-sm)',
    background: 'var(--accent-red)',
    border: 'none',
    color: 'white',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  stopIcon: {
    fontSize: '12px',
    fontWeight: 700,
  },
  inputFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: '8px',
    padding: '0 4px',
  },
  clearBtn: {
    background: 'none',
    border: 'none',
    color: 'var(--text-muted)',
    fontSize: '12px',
    cursor: 'pointer',
    padding: '2px 6px',
    borderRadius: '4px',
  },
  hint: {
    fontSize: '11px',
    color: 'var(--text-muted)',
  },
};

export default ChatPanel;
