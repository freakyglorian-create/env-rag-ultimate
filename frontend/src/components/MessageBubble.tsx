import React from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage } from '../types';
import SourceCard from './SourceCard';

interface MessageBubbleProps {
  message: ChatMessage;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div
      className="fade-in"
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '16px',
        padding: '0 4px',
      }}
    >
      <div
        style={{
          maxWidth: '80%',
          minWidth: isUser ? '80px' : '200px',
        }}
      >
        {/* Message bubble */}
        <div
          style={{
            padding: '12px 16px',
            borderRadius: isUser
              ? 'var(--radius-md) var(--radius-md) 4px var(--radius-md)'
              : 'var(--radius-md) var(--radius-md) var(--radius-md) 4px',
            background: isUser ? 'var(--accent-blue)' : 'var(--bg-secondary)',
            color: isUser ? 'white' : 'var(--text-primary)',
            fontSize: '14px',
            lineHeight: 1.6,
            boxShadow: 'var(--shadow-sm)',
            border: isUser ? 'none' : '1px solid var(--border-color)',
          }}
        >
          {isUser ? (
            <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
          ) : (
            <div className="markdown-body">
              {message.content ? (
                <Markdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </Markdown>
              ) : message.isStreaming ? (
                <span className="pulse" style={{ color: 'var(--text-muted)' }}>
                  正在思考...
                </span>
              ) : null}
            </div>
          )}
        </div>

        {/* Metadata bar for assistant messages */}
        {!isUser && message.metadata && !message.isStreaming && (
          <div style={metadataBarStyle}>
            {message.metadata.model && (
              <span style={metaTagStyle}>
                🤖 {message.metadata.provider}/{message.metadata.model}
              </span>
            )}
            {message.metadata.retrieval_time != null && (
              <span style={metaTagStyle}>
                🔍 检索 {(message.metadata.retrieval_time / 1000).toFixed(2)}s
              </span>
            )}
            {message.metadata.generation_time != null && (
              <span style={metaTagStyle}>
                ⚡ 生成 {(message.metadata.generation_time / 1000).toFixed(2)}s
              </span>
            )}
            {message.metadata.total_time != null && (
              <span style={metaTagStyle}>
                ⏱ 总计 {(message.metadata.total_time / 1000).toFixed(2)}s
              </span>
            )}
          </div>
        )}

        {/* Query rewrite / multi-queries info */}
        {!isUser && message.metadata?.query_rewrite && (
          <div style={rewriteInfoStyle}>
            <span style={rewriteLabelStyle}>Query Rewrite:</span>
            <span style={rewriteValueStyle}>{message.metadata.query_rewrite}</span>
          </div>
        )}
        {!isUser && message.metadata?.multi_queries && message.metadata.multi_queries.length > 0 && (
          <div style={rewriteInfoStyle}>
            <span style={rewriteLabelStyle}>Multi-Queries:</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {message.metadata.multi_queries.map((q, i) => (
                <span key={i} style={rewriteValueStyle}>
                  {i + 1}. {q}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <SourceCard sources={message.sources} />
        )}
      </div>
    </div>
  );
};

const metadataBarStyle: React.CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '8px',
  marginTop: '6px',
  padding: '0 4px',
};

const metaTagStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--text-muted)',
  background: 'var(--bg-tertiary)',
  padding: '2px 8px',
  borderRadius: 'var(--radius-full)',
};

const rewriteInfoStyle: React.CSSProperties = {
  marginTop: '6px',
  padding: '6px 10px',
  background: 'var(--bg-primary)',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border-color)',
  fontSize: '12px',
};

const rewriteLabelStyle: React.CSSProperties = {
  color: 'var(--accent-yellow)',
  fontWeight: 600,
  marginRight: '6px',
};

const rewriteValueStyle: React.CSSProperties = {
  color: 'var(--text-secondary)',
};

export default MessageBubble;
