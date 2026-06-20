import React, { useState, useEffect, useCallback } from 'react';
import type { EvaluationReport } from '../types';
import { runEvaluation, getEvaluationReport } from '../api/client';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Evaluation: React.FC = () => {
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const fetchReport = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getEvaluationReport();
      setReport(data);
    } catch {
      setMessage({ type: 'error', text: '获取评估报告失败' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const handleRun = async () => {
    setRunning(true);
    try {
      await runEvaluation();
      showMessage('success', '评估已完成');
      // Fetch report after running
      setTimeout(fetchReport, 2000);
    } catch (err) {
      showMessage('error', `评估失败: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setRunning(false);
    }
  };

  const toggleExpand = (idx: number) => {
    setExpandedIdx(expandedIdx === idx ? null : idx);
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'var(--accent-green)';
    if (score >= 6) return 'var(--accent-yellow)';
    return 'var(--accent-red)';
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>评估面板</h2>
        <span style={styles.subtitle}>评估 RAG 系统回答质量</span>
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

      {/* Action */}
      <div style={styles.actions}>
        <button
          onClick={handleRun}
          disabled={running}
          style={{
            ...styles.runBtn,
            opacity: running ? 0.5 : 1,
          }}
        >
          {running ? '评估运行中...' : '运行评估'}
        </button>
        <button onClick={fetchReport} style={styles.refreshBtn}>
          刷新报告
        </button>
      </div>

      {/* Loading */}
      {loading && !report && (
        <div style={styles.loading}>加载评估报告中...</div>
      )}

      {/* Report */}
      {report && (
        <div style={styles.report}>
          {/* Average scores */}
          <div style={styles.avgCard}>
            <h3 style={styles.avgTitle}>平均分数</h3>
            <div style={styles.avgGrid}>
              {[
                { label: '相关性', value: report.average_scores.relevance },
                { label: '忠实度', value: report.average_scores.faithfulness },
                { label: '完整性', value: report.average_scores.completeness },
                { label: '清晰度', value: report.average_scores.clarity },
                { label: '总分', value: report.average_scores.total },
              ].map((item) => (
                <div key={item.label} style={styles.avgItem}>
                  <div style={styles.avgLabel}>{item.label}</div>
                  <div style={{ ...styles.avgValue, color: getScoreColor(item.value) }}>
                    {item.value.toFixed(1)}
                  </div>
                </div>
              ))}
            </div>
            <div style={styles.reportMeta}>
              模型: {report.provider}/{report.model} | 时间:{' '}
              {new Date(report.timestamp).toLocaleString('zh-CN')}
            </div>
          </div>

          {/* Results table */}
          <div style={styles.resultsCard}>
            <h3 style={styles.resultsTitle}>评估结果 ({report.results.length} 题)</h3>
            <div style={styles.tableWrapper}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>#</th>
                    <th style={styles.th}>问题</th>
                    <th style={styles.th}>相关性</th>
                    <th style={styles.th}>忠实度</th>
                    <th style={styles.th}>完整性</th>
                    <th style={styles.th}>清晰度</th>
                    <th style={styles.th}>总分</th>
                    <th style={styles.th}>详情</th>
                  </tr>
                </thead>
                <tbody>
                  {report.results.map((r, idx) => (
                    <React.Fragment key={idx}>
                      <tr style={idx % 2 === 0 ? {} : { background: 'rgba(255,255,255,0.02)' }}>
                        <td style={styles.tdCenter}>{idx + 1}</td>
                        <td style={styles.tdQuestion}>{r.question}</td>
                        <td style={styles.tdCenter}>
                          <span style={{ color: getScoreColor(r.scores.relevance) }}>
                            {r.scores.relevance.toFixed(1)}
                          </span>
                        </td>
                        <td style={styles.tdCenter}>
                          <span style={{ color: getScoreColor(r.scores.faithfulness) }}>
                            {r.scores.faithfulness.toFixed(1)}
                          </span>
                        </td>
                        <td style={styles.tdCenter}>
                          <span style={{ color: getScoreColor(r.scores.completeness) }}>
                            {r.scores.completeness.toFixed(1)}
                          </span>
                        </td>
                        <td style={styles.tdCenter}>
                          <span style={{ color: getScoreColor(r.scores.clarity) }}>
                            {r.scores.clarity.toFixed(1)}
                          </span>
                        </td>
                        <td style={styles.tdCenter}>
                          <strong style={{ color: getScoreColor(r.total_score) }}>
                            {r.total_score.toFixed(1)}
                          </strong>
                        </td>
                        <td style={styles.tdCenter}>
                          <button
                            onClick={() => toggleExpand(idx)}
                            style={styles.expandBtn}
                          >
                            {expandedIdx === idx ? '收起' : '展开'}
                          </button>
                        </td>
                      </tr>
                      {expandedIdx === idx && (
                        <tr>
                          <td colSpan={8} style={styles.detailCell}>
                            <div style={styles.detailContent}>
                              <div style={styles.detailSection}>
                                <strong>回答:</strong>
                                <div className="markdown-body" style={{ marginTop: '4px' }}>
                                  <Markdown remarkPlugins={[remarkGfm]}>
                                    {r.answer}
                                  </Markdown>
                                </div>
                              </div>
                              {r.sources && r.sources.length > 0 && (
                                <div style={{ ...styles.detailSection, marginTop: '12px' }}>
                                  <strong>参考来源 ({r.sources.length}):</strong>
                                  {r.sources.map((s, si) => (
                                    <div key={si} style={styles.sourceItem}>
                                      <span style={styles.sourceIdx}>#{si + 1}</span>
                                      <span style={styles.sourceText}>
                                        {s.content.length > 150
                                          ? s.content.slice(0, 150) + '...'
                                          : s.content}
                                      </span>
                                      <span style={styles.sourceScore}>
                                        {(s.score * 100).toFixed(0)}%
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {!loading && !report && (
        <div style={styles.empty}>暂无评估报告，请先运行评估</div>
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
  actions: {
    display: 'flex',
    gap: '10px',
    marginBottom: '24px',
  },
  runBtn: {
    padding: '10px 24px',
    borderRadius: 'var(--radius-sm)',
    border: 'none',
    background: 'var(--accent-blue)',
    color: 'white',
    fontSize: '14px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  refreshBtn: {
    padding: '10px 20px',
    borderRadius: 'var(--radius-sm)',
    border: '1px solid var(--border-color)',
    background: 'var(--bg-secondary)',
    color: 'var(--text-secondary)',
    fontSize: '14px',
    cursor: 'pointer',
  },
  loading: {
    padding: '32px',
    textAlign: 'center',
    color: 'var(--text-muted)',
  },
  empty: {
    padding: '32px',
    textAlign: 'center',
    color: 'var(--text-muted)',
    fontSize: '14px',
  },
  report: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  avgCard: {
    background: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-color)',
    padding: '20px',
  },
  avgTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    marginBottom: '16px',
  },
  avgGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
    gap: '12px',
    marginBottom: '12px',
  },
  avgItem: {
    textAlign: 'center',
    padding: '12px',
    background: 'var(--bg-primary)',
    borderRadius: 'var(--radius-sm)',
  },
  avgLabel: {
    fontSize: '12px',
    color: 'var(--text-muted)',
    marginBottom: '4px',
  },
  avgValue: {
    fontSize: '24px',
    fontWeight: 700,
  },
  reportMeta: {
    fontSize: '12px',
    color: 'var(--text-muted)',
    textAlign: 'right',
  },
  resultsCard: {
    background: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-color)',
    overflow: 'hidden',
  },
  resultsTitle: {
    padding: '14px 16px',
    fontSize: '15px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    borderBottom: '1px solid var(--border-color)',
  },
  tableWrapper: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    padding: '10px 12px',
    textAlign: 'left',
    fontSize: '12px',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    borderBottom: '1px solid var(--border-color)',
    whiteSpace: 'nowrap',
  },
  tdCenter: {
    padding: '10px 12px',
    textAlign: 'center',
    fontSize: '13px',
    color: 'var(--text-secondary)',
    borderBottom: '1px solid var(--border-color)',
    whiteSpace: 'nowrap',
  },
  tdQuestion: {
    padding: '10px 12px',
    fontSize: '13px',
    color: 'var(--text-secondary)',
    borderBottom: '1px solid var(--border-color)',
    maxWidth: '300px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  expandBtn: {
    background: 'none',
    border: '1px solid var(--border-color)',
    borderRadius: '4px',
    color: 'var(--accent-blue)',
    fontSize: '12px',
    padding: '2px 8px',
    cursor: 'pointer',
  },
  detailCell: {
    padding: '16px 20px',
    borderBottom: '1px solid var(--border-color)',
    background: 'var(--bg-primary)',
  },
  detailContent: {
    fontSize: '13px',
  },
  detailSection: {
    color: 'var(--text-primary)',
  },
  sourceItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '8px',
    padding: '6px 0',
    borderBottom: '1px solid var(--border-color)',
  },
  sourceIdx: {
    color: 'var(--accent-green)',
    fontWeight: 600,
    fontSize: '12px',
    flexShrink: 0,
  },
  sourceText: {
    flex: 1,
    color: 'var(--text-secondary)',
    fontSize: '12px',
  },
  sourceScore: {
    color: 'var(--text-muted)',
    fontSize: '11px',
    flexShrink: 0,
  },
};

export default Evaluation;
