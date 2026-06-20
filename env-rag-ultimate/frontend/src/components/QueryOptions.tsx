import React, { useContext } from 'react';
import { AppContext } from '../App';

const QueryOptionsPanel: React.FC = () => {
  const { queryOptions, toggleRewrite, toggleMultiQuery, toggleReranker, setTopK } =
    useContext(AppContext);

  const labelStyle: React.CSSProperties = {
    fontSize: '13px',
    color: 'var(--text-secondary)',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    cursor: 'pointer',
    userSelect: 'none',
  };

  const topKStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '13px',
    color: 'var(--text-secondary)',
  };

  const sliderStyle: React.CSSProperties = {
    width: '80px',
    accentColor: 'var(--accent-blue)',
    cursor: 'pointer',
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
      {/* Query Rewrite */}
      <label style={labelStyle}>
        <span className="toggle-switch">
          <input
            type="checkbox"
            checked={queryOptions.queryRewrite}
            onChange={toggleRewrite}
          />
          <span className="toggle-slider" />
        </span>
        Query Rewrite
      </label>

      {/* Multi-Query */}
      <label style={labelStyle}>
        <span className="toggle-switch">
          <input
            type="checkbox"
            checked={queryOptions.multiQuery}
            onChange={toggleMultiQuery}
          />
          <span className="toggle-slider" />
        </span>
        Multi-Query
      </label>

      {/* Reranker */}
      <label style={labelStyle}>
        <span className="toggle-switch">
          <input
            type="checkbox"
            checked={queryOptions.useReranker}
            onChange={toggleReranker}
          />
          <span className="toggle-slider" />
        </span>
        Reranker
      </label>

      {/* Top-K */}
      <div style={topKStyle}>
        <span>Top-K:</span>
        <input
          type="range"
          min={1}
          max={20}
          value={queryOptions.topK}
          onChange={(e) => setTopK(Number(e.target.value))}
          style={sliderStyle}
        />
        <span style={{ minWidth: '20px', textAlign: 'center' }}>
          {queryOptions.topK}
        </span>
      </div>
    </div>
  );
};

export default QueryOptionsPanel;
