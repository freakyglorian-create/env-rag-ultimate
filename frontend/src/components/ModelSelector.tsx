import React, { useState, useEffect } from 'react';
import type { ModelInfo } from '../types';
import { PROVIDERS } from '../utils/constants';
import { getModels, verifyApiKey } from '../api/client';

interface ModelSelectorProps {
  provider: string;
  model: string;
  apiKey: string;
  onProviderChange: (p: string) => void;
  onModelChange: (m: string) => void;
  onApiKeyChange: (k: string) => void;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({
  provider,
  model,
  apiKey,
  onProviderChange,
  onModelChange,
  onApiKeyChange,
}) => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [keyStatus, setKeyStatus] = useState<'idle' | 'valid' | 'invalid'>('idle');

  // Fetch static model catalog
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
  }, []);

  const providerModels = models.filter((m) => m.provider === provider);

  // Auto-select first model when provider changes
  useEffect(() => {
    const currentExists = providerModels.find((m) => m.model === model);
    if (!currentExists && providerModels.length > 0) {
      onModelChange(providerModels[0].model);
    }
  }, [provider, providerModels, model, onModelChange]);

  // Verify API key
  const handleVerify = async () => {
    if (!apiKey.trim()) return;
    setVerifying(true);
    setKeyStatus('idle');
    try {
      const result = await verifyApiKey({ provider, api_key: apiKey.trim() });
      if (result.valid) {
        setKeyStatus('valid');
        // Auto-select first verified model if current isn't in the list
        if (result.models.length > 0 && !result.models.includes(model)) {
          onModelChange(result.models[0]);
        }
      } else {
        setKeyStatus('invalid');
      }
    } catch {
      setKeyStatus('invalid');
    } finally {
      setVerifying(false);
    }
  };

  // Reset key status when provider changes
  useEffect(() => {
    setKeyStatus('idle');
  }, [provider]);

  const selectStyle: React.CSSProperties = {
    background: 'var(--bg-primary)',
    border: '1px solid var(--border-color)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-primary)',
    fontSize: '13px',
    padding: '6px 10px',
    outline: 'none',
    cursor: 'pointer',
  };

  const inputStyle: React.CSSProperties = {
    background: 'var(--bg-primary)',
    border: '1px solid var(--border-color)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-primary)',
    fontSize: '13px',
    padding: '6px 10px',
    outline: 'none',
    width: '200px',
  };

  const btnStyle: React.CSSProperties = {
    background: keyStatus === 'valid' ? 'var(--accent-green)' :
                keyStatus === 'invalid' ? 'var(--accent-red)' :
                'var(--accent-blue)',
    border: 'none',
    borderRadius: 'var(--radius-sm)',
    color: '#fff',
    fontSize: '12px',
    padding: '6px 12px',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  };

  const statusDot = keyStatus === 'valid' ? '🟢' :
                    keyStatus === 'invalid' ? '🔴' : '';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
      {/* Provider selector */}
      <select
        value={provider}
        onChange={(e) => onProviderChange(e.target.value)}
        style={{ ...selectStyle, minWidth: '140px' }}
      >
        {PROVIDERS.map((p) => (
          <option key={p.value} value={p.value}>
            {p.label}
          </option>
        ))}
      </select>

      {/* API Key input */}
      <input
        type="password"
        value={apiKey}
        onChange={(e) => onApiKeyChange(e.target.value)}
        placeholder="输入 API Key"
        style={inputStyle}
        onKeyDown={(e) => { if (e.key === 'Enter') handleVerify(); }}
      />

      {/* Verify button */}
      <button
        onClick={handleVerify}
        disabled={verifying || !apiKey.trim()}
        style={btnStyle}
      >
        {verifying ? '验证中…' :
         keyStatus === 'valid' ? `${statusDot} 已验证` :
         keyStatus === 'invalid' ? `${statusDot} 验证失败` :
         '验证 Key'}
      </button>

      {/* Model selector */}
      <select
        value={model}
        onChange={(e) => onModelChange(e.target.value)}
        style={{ ...selectStyle, minWidth: '160px' }}
        disabled={loading}
      >
        {providerModels.length === 0 ? (
          <option value="">(无可用模型)</option>
        ) : (
          providerModels.map((m) => (
            <option key={m.model} value={m.model}>
              {m.model}
            </option>
          ))
        )}
      </select>

      {loading && (
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>⟳</span>
      )}
    </div>
  );
};

export default ModelSelector;
