import React, { useState, useEffect, useRef, useCallback } from 'react';
import type { KBDocument } from '../types';
import { SUPPORTED_UPLOAD_FORMATS } from '../utils/constants';
import { getDocuments, uploadDocument, buildKnowledgeBase, loadKnowledgeBase } from '../api/client';

const KnowledgeBase: React.FC = () => {
  const [documents, setDocuments] = useState<KBDocument[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [building, setBuilding] = useState(false);
  const [loadingKB, setLoadingKB] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch {
      setMessage({ type: 'error', text: '获取文档列表失败' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleUpload = async (files: FileList | File[]) => {
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        await uploadDocument(file);
      }
      showMessage('success', `成功上传 ${files.length} 个文件`);
      fetchDocuments();
    } catch (err) {
      showMessage('error', `上传失败: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setUploading(false);
    }
  };

  const handleBuild = async () => {
    setBuilding(true);
    try {
      const result = await buildKnowledgeBase();
      showMessage('success', result.message);
      fetchDocuments();
    } catch (err) {
      showMessage('error', `构建失败: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setBuilding(false);
    }
  };

  const handleLoad = async () => {
    setLoadingKB(true);
    try {
      const result = await loadKnowledgeBase();
      showMessage('success', result.message);
    } catch (err) {
      showMessage('error', `加载失败: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoadingKB(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      handleUpload(e.dataTransfer.files);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>知识库管理</h2>
        <span style={styles.subtitle}>管理文档和知识库构建</span>
      </div>

      {/* Message */}
      {message && (
        <div
          style={{
            ...styles.message,
            borderLeft: `4px solid ${message.type === 'success' ? 'var(--accent-green)' : 'var(--accent-red)'}`,
          }}
        >
          {message.text}
        </div>
      )}

      {/* Upload area */}
      <div
        style={{
          ...styles.uploadArea,
          borderColor: dragOver ? 'var(--accent-blue)' : 'var(--border-color)',
          background: dragOver ? 'rgba(59, 130, 246, 0.05)' : 'var(--bg-secondary)',
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          style={{ display: 'none' }}
          onChange={(e) => e.target.files && handleUpload(e.target.files)}
          accept={SUPPORTED_UPLOAD_FORMATS.join(',')}
        />
        <div style={styles.uploadIcon}>📄</div>
        <div style={styles.uploadText}>
          {uploading ? '上传中...' : '拖拽文件到此处或点击上传'}
        </div>
        <div style={styles.uploadHint}>
          支持格式: {SUPPORTED_UPLOAD_FORMATS.join(', ')}
        </div>
      </div>

      {/* Action buttons */}
      <div style={styles.actions}>
        <button
          onClick={handleBuild}
          disabled={building || documents.length === 0}
          style={{
            ...styles.actionBtn,
            background: building ? 'var(--bg-tertiary)' : 'var(--accent-blue)',
            opacity: building || documents.length === 0 ? 0.5 : 1,
          }}
        >
          {building ? '构建中...' : '构建知识库'}
        </button>
        <button
          onClick={handleLoad}
          disabled={loadingKB}
          style={{
            ...styles.actionBtn,
            background: loadingKB ? 'var(--bg-tertiary)' : 'var(--accent-green)',
            opacity: loadingKB ? 0.5 : 1,
          }}
        >
          {loadingKB ? '加载中...' : '加载知识库'}
        </button>
        <button onClick={fetchDocuments} style={{ ...styles.actionBtn, background: 'var(--bg-tertiary)' }}>
          刷新列表
        </button>
      </div>

      {/* Documents table */}
      <div style={styles.tableContainer}>
        <h3 style={styles.tableTitle}>
          已加载文档 ({documents.length})
        </h3>
        {loading ? (
          <div style={styles.loading}>加载中...</div>
        ) : documents.length === 0 ? (
          <div style={styles.empty}>暂无文档，请先上传文件</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>文件名</th>
                <th style={styles.th}>大小</th>
                <th style={styles.th}>分块数</th>
                <th style={styles.th}>上传时间</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc, idx) => (
                <tr key={idx} style={idx % 2 === 0 ? {} : { background: 'rgba(255,255,255,0.02)' }}>
                  <td style={styles.td}>
                    <span style={styles.fileIcon}>📄</span>
                    {doc.filename}
                  </td>
                  <td style={styles.td}>{formatFileSize(doc.size)}</td>
                  <td style={styles.td}>{doc.chunks ?? '-'}</td>
                  <td style={styles.td}>
                    {new Date(doc.uploaded_at).toLocaleString('zh-CN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
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
    fontSize: '14px',
    color: 'var(--text-muted)',
  },
  message: {
    padding: '10px 14px',
    background: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-sm)',
    fontSize: '13px',
    color: 'var(--text-primary)',
    marginBottom: '16px',
  },
  uploadArea: {
    border: '2px dashed var(--border-color)',
    borderRadius: 'var(--radius-md)',
    padding: '32px',
    textAlign: 'center',
    cursor: 'pointer',
    marginBottom: '16px',
    transition: 'var(--transition)',
  },
  uploadIcon: {
    fontSize: '36px',
    marginBottom: '8px',
  },
  uploadText: {
    fontSize: '14px',
    color: 'var(--text-secondary)',
    marginBottom: '4px',
  },
  uploadHint: {
    fontSize: '12px',
    color: 'var(--text-muted)',
  },
  actions: {
    display: 'flex',
    gap: '10px',
    marginBottom: '24px',
    flexWrap: 'wrap',
  },
  actionBtn: {
    padding: '8px 20px',
    borderRadius: 'var(--radius-sm)',
    border: 'none',
    color: 'white',
    fontSize: '13px',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'var(--transition)',
  },
  tableContainer: {
    background: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-color)',
    overflow: 'hidden',
  },
  tableTitle: {
    padding: '14px 16px',
    fontSize: '15px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    borderBottom: '1px solid var(--border-color)',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    padding: '10px 16px',
    textAlign: 'left',
    fontSize: '12px',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    borderBottom: '1px solid var(--border-color)',
  },
  td: {
    padding: '10px 16px',
    fontSize: '13px',
    color: 'var(--text-secondary)',
    borderBottom: '1px solid var(--border-color)',
  },
  fileIcon: {
    marginRight: '6px',
  },
  loading: {
    padding: '24px',
    textAlign: 'center',
    color: 'var(--text-muted)',
  },
  empty: {
    padding: '32px',
    textAlign: 'center',
    color: 'var(--text-muted)',
    fontSize: '14px',
  },
};

export default KnowledgeBase;
