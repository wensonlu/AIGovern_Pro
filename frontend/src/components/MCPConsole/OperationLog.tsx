import React from 'react';
import { Tag, Tooltip } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined, CameraOutlined } from '@ant-design/icons';
import styles from './OperationLog.module.css';

interface Operation {
  type: string;
  sequence?: number;
  tool?: string;
  params?: Record<string, any>;
  message?: string;
  success?: boolean;
  error?: string;
  content?: string;
  task?: string;
}

interface OperationLogProps {
  operations: Operation[];
}

const OperationLog: React.FC<OperationLogProps> = ({ operations }) => {
  const getOperationIcon = (type: string, success?: boolean) => {
    switch (type) {
      case 'tool_call':
        return <LoadingOutlined />;
      case 'tool_result':
        return success ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'screenshot':
        return <CameraOutlined />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'done':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      default:
        return null;
    }
  };

  const getToolName = (tool?: string) => {
    if (!tool) return 'Unknown';
    return tool
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const formatParams = (params?: Record<string, any>) => {
    if (!params || Object.keys(params).length === 0) return null;
    return Object.entries(params)
      .map(([key, value]) => {
        const displayValue = typeof value === 'string' && value.length > 30
          ? value.substring(0, 30) + '...'
          : JSON.stringify(value);
        return `${key}: ${displayValue}`;
      })
      .join(', ');
  };

  return (
    <div className={styles.log}>
      {operations.map((op, idx) => (
        <div key={idx} className={`${styles.entry} ${styles[op.type]}`}>
          <div className={styles.icon}>{getOperationIcon(op.type, op.success)}</div>

          <div className={styles.content}>
            <div className={styles.header}>
              <span className={styles.type}>{op.type.toUpperCase()}</span>
              {op.sequence && <Tag>{op.sequence}</Tag>}
            </div>

            <div className={styles.body}>
              {op.type === 'tool_call' && (
                <>
                  <div className={styles.label}>{getToolName(op.tool)}</div>
                  {formatParams(op.params) && (
                    <Tooltip title={formatParams(op.params)}>
                      <div className={styles.params}>{formatParams(op.params)}</div>
                    </Tooltip>
                  )}
                </>
              )}

              {op.type === 'tool_result' && (
                <>
                  <div className={styles.message}>{op.message}</div>
                  {op.error && <div className={styles.error}>{op.error}</div>}
                </>
              )}

              {op.type === 'screenshot' && (
                <div className={styles.label}>Screenshot captured</div>
              )}

              {op.type === 'response' && (
                <div className={styles.message}>{op.content?.substring(0, 100)}...</div>
              )}

              {op.type === 'task' && (
                <div className={styles.task}>{op.task}</div>
              )}

              {op.type === 'error' && (
                <div className={styles.error}>{op.message}</div>
              )}

              {op.type === 'done' && (
                <div className={styles.label}>Task completed ({op.tool_calls || 0} operations)</div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default OperationLog;
