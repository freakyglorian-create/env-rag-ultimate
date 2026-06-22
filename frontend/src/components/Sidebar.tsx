import React, { useState, useEffect } from 'react';
import type { NavPage } from '../types';
import { APP_NAME, NAV_ITEMS } from '../utils/constants';
import { getSystemStatus } from '../api/client';

interface SidebarProps {
  currentPage: NavPage;
  onPageChange: (page: NavPage) => void;
  currentModel: string;
  currentProvider: string;
}

const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onPageChange,
  currentModel,
  currentProvider,
}) => {
  const [kbLoaded, setKbLoaded] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const status = await getSystemStatus();
        setKbLoaded(status.knowledge_base_loaded);
      } catch {
        setKbLoaded(false);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.logoArea}>
        <div style={styles.logoIcon}>🌍</div>
        <div style={styles.logoText}>
          <div style={styles.logoTitle}>{APP_NAME}</div>
          <div style={styles.logoSub}>RAG Q&A System</div>
        </div>
      </div>

      <nav style={styles.nav}>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.page}
            onClick={() => onPageChange(item.page)}
            style={{
              ...styles.navItem,
              ...(currentPage === item.page ? styles.navItemActive : {}),
            }}
          >
            <span style={styles.navIcon}>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div style={styles.bottomArea}>
        <div style={styles.divider} />
        <div style={styles.statusSection}>
          <div style={styles.statusRow}>
            <span style={styles.statusLabel}>当前模型</span>
            <span style={styles.statusValue}>
              {currentProvider}/{currentModel || '-'}
            </span>
          </div>
          <div style={styles.statusRow}>
            <span style={styles.statusLabel}>知识库</span>
            <span style={styles.statusValue}>
              <span
                style={{
                  ...styles.statusDot,
                  background: kbLoaded ? 'var(--accent-green)' : 'var(--accent-red)',
                }}
              />
              {kbLoaded ? '已加载' : '未加载'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: 'var(--sidebar-width)',
    height: '100%',
    background: 'var(--bg-secondary)',
    borderRight: '1px solid var(--border-color)',
    display: 'flex',
    flexDirection: 'column',
    flexShrink: 0,
  },
  logoArea: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '20px 16px 16px',
  },
  logoIcon: { fontSize: '28px', flexShrink: 0 },
  logoText: { display: 'flex', flexDirection: 'column' },
  logoTitle: { fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.3 },
  logoSub: { fontSize: '11px', color: 'var(--text-muted)' },
  nav: {
    flex: 1,
    padding: '8px 10px',
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '10px 14px',
    borderRadius: 'var(--radius-sm)',
    border: 'none',
    background: 'transparent',
    color: 'var(--text-secondary)',
    fontSize: '14px',
    cursor: 'pointer',
    transition: 'var(--transition)',
    textAlign: 'left',
    width: '100%',
  },
  navItemActive: {
    background: 'var(--accent-blue)',
    color: 'white',
  },
  navIcon: { fontSize: '16px', width: '20px', textAlign: 'center' },
  bottomArea: { padding: '0 16px 16px' },
  divider: {
    height: '1px',
    background: 'var(--border-color)',
    marginBottom: '12px',
  },
  statusSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  statusRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '12px',
  },
  statusLabel: { color: 'var(--text-muted)' },
  statusValue: {
    color: 'var(--text-secondary)',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    display: 'inline-block',
  },
};

export default Sidebar;
