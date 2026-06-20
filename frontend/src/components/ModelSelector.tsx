import React, { useState, useEffect } from 'react';
import type { ModelInfo } from '../types';
import { PROVIDERS } from '../utils/constants';
import { getModels } from '../api/client';

interface ModelSelectorProps {
  provider: string;
  model: string;
  onProviderChange: (p: string) => void;
  onModelChange: (m: string) => void;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({
  provider,
  model,
  onProviderChange,
  onModelChange,
}) => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchModels = async () => {
      setLoading(true);
      try {
        const data = await getModels();
        setModels(data);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    fetchModels();
    const interval = setInterval(fetchModels, 60000);
    return () => clearInterval(interval);
  }, []);

  const providerModels = models.filter((m) => m.provider === provider);

  // Auto-select first available model when provider changes
  useEffect(() => {
    if (providerModels.length > 0 && !providerModels.find((m) => m.model === model)) {
      const firstAvailable = providerModels.find((m) => m.available);
      if (firstAvailable) {
        onModelChange(firstAvailable.model);
      }
    }
  }, [provider, providerModels, model, onModelChange]);

  const selectStyle: React.CSSProperties = {
    background: 'var(--bg-primary)',
    border: '1px solid var(--border-color)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-primary)',
    fontSize: '13px',
    padding: '6px 10px',
    outline: 'none',
    cursor: 'pointer',
    minWidth: '120px',
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <select
        value={provider}
        onChange={(e) => onProviderChange(e.target.value)}
        style={selectStyle}
      >
        {PROVIDERS.map((p) => (
          <option key={p.value} value={p.value}>
            {p.label}
          </option>
        ))}
      </select>

      <select
        value={model}
        onChange={(e) => onModelChange(e.target.value)}
        style={{ ...selectStyle, minWidth: '160px' }}
        disabled={loading}
      >
        {providerModels.length === 0 ? (
          <option value="">无可用模型</option>
        ) : (
          providerModels.map((m) => (
            <option key={m.model} value={m.model}>
              {m.model}
              {m.is_local ? ' (本地)' : ''}
            </option>
          ))
        )}
      </select>

      {/* Availability indicator */}
      {model && (() => {
        const currentModel = models.find(
          (m) => m.provider === provider && m.model === model,
        );
        if (!currentModel) return null;
        return (
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: currentModel.available
                ? 'var(--accent-green)'
                : 'var(--accent-red)',
              display: 'inline-block',
              flexShrink: 0,
            }}
            title={currentModel.available ? '可用' : '不可用'}
          />
        );
      })()}

      {loading && (
        <span className="spinner" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          ⟳
        </span>
      )}
    </div>
  );
};

export default ModelSelector;
