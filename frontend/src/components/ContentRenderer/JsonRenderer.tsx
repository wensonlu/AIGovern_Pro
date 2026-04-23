import React, { useState } from 'react';
import { ContentRendererProps } from './types';

const JsonRenderer: React.FC<ContentRendererProps> = ({ content, className }) => {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  let parsedData: unknown;
  try {
    parsedData = JSON.parse(content);
  } catch (e) {
    return (
      <div className={className} style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '12px' }}>
        <span style={{ color: '#d32f2f' }}>Invalid JSON:</span>
        {'\n'}
        {content}
      </div>
    );
  }

  const toggleKey = (key: string) => {
    const newExpanded = new Set(expandedKeys);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedKeys(newExpanded);
  };

  const renderValue = (value: unknown, path: string = 'root', depth: number = 0): React.ReactNode => {
    const isExpanded = expandedKeys.has(path);
    const indent = depth * 16;

    if (value === null) {
      return <span style={{ color: '#d32f2f' }}>null</span>;
    }

    if (typeof value === 'boolean') {
      return <span style={{ color: '#1976d2' }}>{String(value)}</span>;
    }

    if (typeof value === 'number') {
      return <span style={{ color: '#388e3c' }}>{value}</span>;
    }

    if (typeof value === 'string') {
      return <span style={{ color: '#d32f2f' }}>&quot;{value}&quot;</span>;
    }

    if (Array.isArray(value)) {
      return (
        <div>
          <div onClick={() => toggleKey(path)} style={{ cursor: 'pointer', paddingLeft: `${indent}px`, userSelect: 'none' }}>
            <span style={{ marginRight: '4px' }}>{isExpanded ? '▼' : '▶'}</span>
            <span>[ {value.length} items ]</span>
          </div>
          {isExpanded && value.map((item, idx) => (
            <div key={idx} style={{ paddingLeft: `${indent + 16}px` }}>
              <span style={{ color: '#666' }}>[{idx}]:</span> {renderValue(item, `${path}[${idx}]`, depth + 1)}
            </div>
          ))}
        </div>
      );
    }

    if (typeof value === 'object') {
      const entries = Object.entries(value as Record<string, unknown>);
      return (
        <div>
          <div onClick={() => toggleKey(path)} style={{ cursor: 'pointer', paddingLeft: `${indent}px`, userSelect: 'none' }}>
            <span style={{ marginRight: '4px' }}>{isExpanded ? '▼' : '▶'}</span>
            <span>{`{ ${entries.length} properties }`}</span>
          </div>
          {isExpanded && entries.map(([key, val]) => (
            <div key={key} style={{ paddingLeft: `${indent + 16}px` }}>
              <span style={{ color: '#1976d2' }}>&quot;{key}&quot;:</span> {renderValue(val, `${path}.${key}`, depth + 1)}
            </div>
          ))}
        </div>
      );
    }

    return <span>{String(value)}</span>;
  };

  return (
    <div className={className} style={{ fontFamily: 'monospace', fontSize: '12px', lineHeight: '1.6', color: '#333' }}>
      {renderValue(parsedData)}
    </div>
  );
};

JsonRenderer.displayName = 'JsonRenderer';

export default JsonRenderer;
