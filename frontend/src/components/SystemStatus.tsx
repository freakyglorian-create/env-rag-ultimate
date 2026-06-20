import React, { useState, useEffect, useCallback } from 'react';
import type { SystemStatus as SystemStatusType } from '../types';
import { getSystemStatus } from '../api/client';

const SystemStatusPanel: React.FC = () => {
  const [status, setStatus] = useState<SystemStatusType | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await getSystemStatus();
      setStatus(data);
      setLastUpdated(new Date());
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const getStatusColor = (value: string) => {
    if (value === 'running' || value === 'loaded' || value === 'active') return 'var(--accent-green)';
    if (value === 'stopped' || value === 'not loaded') return 'var(--accent-red)';
    return 'var(--accent-yellow)';
  };

  const InfoRow: React.FC<{
    label: string;
    value: string;
    isStatus?: boolean;
  }> = ({ label, value, isStatus }) => (
    <div style={infoRowStyle}>
      <span style={infoLabelStyle}>{label}</span>
      <span style={infoValueStyle}>
        {isStatus && (
          <span
            style={{
              ...statusDotStyle,
              background: getStatusColor(value),
            }}
          />
        )}
        {value}
      </span>
    </div>
  );

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>系统状态</h2>
        <span style={styles.subtitle}>
          {lastUpdated
            ? `最后更新: ${lastUpdated.toLocaleTimeString('zh-CN')}`
            : ''}
        </span>
      </div>

      {loading && !status ? (
        <div style={styles.loading}>加载中...</div>
      ) : status ? (
        <div style={styles.content}>
          {/* System Info Card */}
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>系统信息</h3>
            <InfoRow label="系统版本" value={status.version} />
          </div>

          {/* Knowledge Base Card */}
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>知识库状态</h3>
            <InfoRow
              label="加载状态"
              value={status.knowledge_base.loaded ? '已加载' : '未加载'}
              isStatus
            />
            <InfoRow label="文档数量" value={String(status.knowledge_base.document_count)} />
            <InfoRow label="分块数量" value={String(status.knowledge_base.chunk_count)} />
            {status.knowledge_base.last_built && (
              <InfoRow
                label="最后构建"
                value={new Date(status.knowledge_base.last_built).toLocaleString('zh-CN')}
              />
            )}
          </div>

          {/* Models Card */}
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>模型配置</h3>
            <InfoRow label="Embedding 模型" value={status.embedding_model} />
            <InfoRow
              label="Reranker"
              value={status.reranker_status}
              isStatus
            />
            <InfoRow
              label="Ollama"
              value={
                status.ollama_status === 'running'
                  ? '运行中'
                  : status.ollama_status === 'stopped'
                    ? '已停止'
                    : '未知'
              }
              isStatus
            />
          </div>

          {/* Models List Card */}
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>
              可用模型 ({status.models.length})
            </h3>
            <div style={styles.modelList}>
              {status.models.map((m, idx) => (
                <div
                  key={idx}
                  style={{
                    ...styles.modelItem,
                    borderLeftColor: m.available ? 'var(--accent-green)' : 'var(--accent-red)',
                  }}
                >
                  <div style={styles.modelHeader}>
                    <span
                      style={{
                        ...statusDotStyle,
                        background: m.available ? 'var(--accent-green)' : 'var(--accent-red)',
                      }}
                    />
                    <span style={styles.modelName}>{m.model}</span>
                    {m.is_local && (
                      <span style={styles.localTag}>本地</span>
                    )}
                  </div>
                  <div style={styles.modelProvider}>{m.provider}</div>
                </div>
              ))}
              {status.models.length === 0 && (
                <div style={styles.emptyModels}>暂无可用模型</div>
              )}
            </div>
          </div>

          {/* Refresh button */}
          <button onClick={fetchStatus} style={styles.refreshBtn}>
            刷新状态
          </button>
        </div>
      ) : (
        <div style={styles.error}>无法获取系统状态</div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '24px',
    overflowY: 'auto',
    height: '100%',
  },
  header: {
    marginBottom: '24px',
  },
  title: {
    fontSize: '22px',
    fontWeight: 700,
    color: 'var(--text-primary)',
    marginBottom: '4px',
  },
  subtitle: {
    fontSize: '13px',
    color: 'var(--text-muted)',
  },
  loading: {
    padding: '32px',
    textAlign: 'center',
    color: 'var(--text-muted)',
  },
  error: {
    padding: '32px',
    textAlign: 'center',
    color: 'var(--accent-red)',
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  card: {
    background: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-color)',
    padding: '20px',
  },
  cardTitle: {
    fontSize: '15px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    marginBottom: '14px',
    paddingBottom: '10px',
    borderBottom: '1px solid var(--border-color)',
  },
  modelList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  modelItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 12px',
    background: 'var(--bg-primary)',
    borderRadius: 'var(--radius-sm)',
    borderLeft: '3px solid',
  },
  modelHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  modelName: {
    fontSize: '13px',
    fontWeight: 600,
    color: 'var(--text-primary)',
  },
  modelProvider: {
    fontSize: '12px',
    color: 'var(--text-muted)',
  },
  localTag: {
    fontSize: '10px',
    padding: '1px 6px',
    background: 'var(--accent-green)',
    color: 'white',
    borderRadius: 'var(--radius-full)',
    fontWeight: 600,
  },
  emptyModels: {
    padding: '16px',
    textAlign: 'center',
    color: 'var(--text-muted)',
    fontSize: '13px',
  },
  refreshBtn: {
    padding: '10px 20px',
    borderRadius: 'var(--radius-sm)',
    border: '1px solid var(--border-color)',
    background: 'var(--bg-secondary)',
    color: 'var(--text-secondary)',
    fontSize: '14px',
    cursor: 'pointer',
    alignSelf: 'flex-start',
  },
};

const infoRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '8px 0',
  borderBottom: '1px solid var(--border-color)',
};

const infoLabelStyle: React.CSSProperties = {
  fontSize: '13px',
  color: 'var(--text-muted)',
};

const infoValueStyle: React.CSSProperties = {
  fontSize: '13px',
  color: 'var(--text-primary)',
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
};

const statusDotStyle: React.CSSProperties = {
  width: '8px',
  height: '8px',
  borderRadius: '50%',
  display: 'inline-block',
};

export default SystemStatusPanel;
