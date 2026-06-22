import React from 'react';
import type { SourceDocument } from '../types';

interface SourceCardProps {
  sources: SourceDocument[];
}

const SourceCard: React.FC<SourceCardProps> = ({ sources }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.icon}>📎</span>
        <span style={styles.title}>参考资料 ({sources.length})</span>
      </div>
      <div style={styles.list}>
        {sources.map((source, idx) => (
          <div key={idx} style={styles.card}>
            <div style={styles.cardHeader}>
              <span style={styles.cardIndex}>#{idx + 1}</span>
              <span style={styles.sourceFile}>📄 {source.source}</span>
            </div>
            <div style={styles.content}>
              {source.content.length > 200
                ? source.content.slice(0, 200) + '...'
                : source.content}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginTop: '8px',
    padding: '10px 12px',
    background: 'var(--bg-primary)',
    borderRadius: 'var(--radius-sm)',
    border: '1px solid var(--border-color)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    marginBottom: '8px',
    fontSize: '12px',
    color: 'var(--text-secondary)',
  },
  icon: { fontSize: '14px' },
  title: { fontWeight: 600 },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  card: {
    padding: '8px 10px',
    background: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-sm)',
    borderLeft: '3px solid var(--accent-green)',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '4px',
  },
  cardIndex: {
    fontSize: '11px',
    fontWeight: 700,
    color: 'var(--accent-green)',
  },
  sourceFile: {
    fontSize: '11px',
    color: 'var(--text-muted)',
  },
  content: {
    fontSize: '12px',
    color: 'var(--text-secondary)',
    lineHeight: 1.5,
  },
};

export default SourceCard;
