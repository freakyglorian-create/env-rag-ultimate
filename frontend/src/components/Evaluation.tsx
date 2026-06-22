import React, { useState, useEffect, useCallback } from 'react';
import { runEvaluation, getEvaluationReport } from '../api/client';
import { useAppContext } from '../App';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface EvalResult {
  question: string;
  ground_truth: string;
  answer: string;
  scores: Record<string, number>;
  category: string;
  error?: string;
}

interface EvalReport {
  total_questions: number;
  evaluated: number;
  average_scores: Record<string, number>;
  per_question: EvalResult[];
  generated_at: string;
}

const Evaluation: React.FC = () => {
  const { apiKey, provider, model } = useAppContext();
  const [report, setReport] = useState<EvalReport | null>(null);
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
      if (data) {
        setReport(data);
      }
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
    if (!apiKey.trim()) {
      showMessage('error', '请先在对话页顶部输入 API Key');
      return;
    }
    setRunning(true);
    try {
      const result = await runEvaluation({ provider, model, api_key: apiKey });
      // 后端直接返回完整报告，无需二次请求
      setReport(result);
      showMessage('success', `评估完成: ${result.evaluated}/${result.total_questions} 题`);
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
    if (score >= 0.8) return 'var(--accent-green)';
    if (score >= 0.5) return 'var(--accent-yellow)';
    return 'var(--accent-red)';
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>评估面板</h2>
        <span style={styles.subtitle}>评估 RAG 系统回答质量</span>
      </div>

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

      <div style={styles.actions}>
        <button
          onClick={handleRun}
          disabled={running || !apiKey.trim()}
          style={{ ...styles.runBtn, opacity: running || !apiKey.trim() ? 0.5 : 1 }}
        >
          {running ? '评估运行中...' : '运行评估'}
        </button>
        <button onClick={fetchReport} style={styles.refreshBtn}>刷新报告</button>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)', alignSelf: 'center' }}>
          {apiKey ? `模型: ${provider}/${model || 'default'}` : '⚠ 请先在对话页输入 API Key'}
        </span>
      </div>

      {loading && !report && (
        <div style={styles.loading}>加载评估报告中...</div>
      )}

      {report && (
        <div style={styles.report}>
          <div style={styles.avgCard}>
            <h3 style={styles.avgTitle}>平均分数</h3>
            <div style={styles.avgGrid}>
              {Object.entries(report.average_scores).map(([key, value]) => (
                <div key={key} style={styles.avgItem}>
                  <div style={styles.avgLabel}>{key}</div>
                  <div style={{ ...styles.avgValue, color: getScoreColor(value) }}>
                    {value.toFixed(3)}
                  </div>
                </div>
              ))}
            </div>
            <div style={styles.reportMeta}>
              评估时间: {new Date(report.generated_at).toLocaleString('zh-CN')}
            </div>
          </div>

          <div style={styles.resultsCard}>
            <h3 style={styles.resultsTitle}>
              评估结果 ({report.evaluated}/{report.total_questions} 题)
            </h3>
            <div style={styles.tableWrapper}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>#</th>
                    <th style={styles.th}>问题</th>
                    <th style={styles.th}>类别</th>
                    <th style={styles.th}>整体分</th>
                    <th style={styles.th}>详情</th>
                  </tr>
                </thead>
                <tbody>
                  {report.per_question.map((r, idx) => (
                    <React.Fragment key={idx}>
                      <tr style={idx % 2 === 0 ? {} : { background: 'rgba(255,255,255,0.02)' }}>
                        <td style={styles.tdCenter}>{idx + 1}</td>
                        <td style={styles.tdQuestion}>{r.question}</td>
                        <td style={styles.tdCenter}>{r.category || '-'}</td>
                        <td style={styles.tdCenter}>
                          {r.error ? (
                            <span style={{ color: 'var(--accent-red)' }}>ERROR</span>
                          ) : (
                            <strong style={{ color: getScoreColor(r.scores?.overall ?? 0) }}>
                              {(r.scores?.overall ?? 0).toFixed(3)}
                            </strong>
                          )}
                        </td>
                        <td style={styles.tdCenter}>
                          <button onClick={() => toggleExpand(idx)} style={styles.expandBtn}>
                            {expandedIdx === idx ? '收起' : '展开'}
                          </button>
                        </td>
                      </tr>
                      {expandedIdx === idx && !r.error && (
                        <tr>
                          <td colSpan={5} style={styles.detailCell}>
                            <div style={styles.detailContent}>
                              <div style={styles.detailSection}>
                                <strong>标准答案:</strong>
                                <div style={{ marginTop: '4px', color: 'var(--text-secondary)' }}>
                                  {r.ground_truth}
                                </div>
                              </div>
                              <div style={{ ...styles.detailSection, marginTop: '12px' }}>
                                <strong>模型回答:</strong>
                                <div className="markdown-body" style={{ marginTop: '4px' }}>
                                  <Markdown remarkPlugins={[remarkGfm]}>{r.answer}</Markdown>
                                </div>
                              </div>
                              {r.scores && (
                                <div style={{ ...styles.detailSection, marginTop: '12px' }}>
                                  <strong>详细评分:</strong>
                                  <div style={styles.scoresGrid}>
                                    {Object.entries(r.scores).map(([k, v]) => (
                                      <span key={k} style={styles.scoreTag}>
                                        {k}: {v.toFixed(3)}
                                      </span>
                                    ))}
                                  </div>
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
  container: { padding: '24px', overflowY: 'auto', height: '100%' },
  header: { marginBottom: '24px' },
  title: { fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' },
  subtitle: { fontSize: '14px', color: 'var(--text-muted)' },
  message: {
    padding: '10px 14px', background: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-sm)', fontSize: '13px',
    color: 'var(--text-primary)', marginBottom: '16px',
  },
  actions: { display: 'flex', gap: '10px', marginBottom: '24px' },
  runBtn: {
    padding: '10px 24px', borderRadius: 'var(--radius-sm)', border: 'none',
    background: 'var(--accent-blue)', color: 'white', fontSize: '14px',
    fontWeight: 600, cursor: 'pointer',
  },
  refreshBtn: {
    padding: '10px 20px', borderRadius: 'var(--radius-sm)',
    border: '1px solid var(--border-color)', background: 'var(--bg-secondary)',
    color: 'var(--text-secondary)', fontSize: '14px', cursor: 'pointer',
  },
  loading: { padding: '32px', textAlign: 'center', color: 'var(--text-muted)' },
  empty: { padding: '32px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '14px' },
  report: { display: 'flex', flexDirection: 'column', gap: '20px' },
  avgCard: {
    background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-color)', padding: '20px',
  },
  avgTitle: { fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '16px' },
  avgGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '12px', marginBottom: '12px' },
  avgItem: { textAlign: 'center', padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-sm)' },
  avgLabel: { fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' },
  avgValue: { fontSize: '24px', fontWeight: 700 },
  reportMeta: { fontSize: '12px', color: 'var(--text-muted)', textAlign: 'right' },
  resultsCard: {
    background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-color)', overflow: 'hidden',
  },
  resultsTitle: {
    padding: '14px 16px', fontSize: '15px', fontWeight: 600,
    color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)',
  },
  tableWrapper: { overflowX: 'auto' },
  table: { width: '100%', borderCollapse: 'collapse' as const },
  th: {
    padding: '10px 12px', textAlign: 'left' as const, fontSize: '12px',
    fontWeight: 600, color: 'var(--text-muted)',
    borderBottom: '1px solid var(--border-color)', whiteSpace: 'nowrap' as const,
  },
  tdCenter: {
    padding: '10px 12px', textAlign: 'center' as const, fontSize: '13px',
    color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-color)',
    whiteSpace: 'nowrap' as const,
  },
  tdQuestion: {
    padding: '10px 12px', fontSize: '13px', color: 'var(--text-secondary)',
    borderBottom: '1px solid var(--border-color)',
    maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const,
  },
  expandBtn: {
    background: 'none', border: '1px solid var(--border-color)',
    borderRadius: '4px', color: 'var(--accent-blue)',
    fontSize: '12px', padding: '2px 8px', cursor: 'pointer',
  },
  detailCell: { padding: '16px 20px', borderBottom: '1px solid var(--border-color)', background: 'var(--bg-primary)' },
  detailContent: { fontSize: '13px' },
  detailSection: { color: 'var(--text-primary)' },
  scoresGrid: { display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' },
  scoreTag: {
    fontSize: '11px', color: 'var(--text-secondary)',
    background: 'var(--bg-secondary)', padding: '2px 8px', borderRadius: 'var(--radius-full)',
  },
};

export default Evaluation;
