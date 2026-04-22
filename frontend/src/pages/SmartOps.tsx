import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Table, Tag, Modal, Form, Input, Select, Empty, Timeline, Alert, message } from 'antd';
import { PlayCircleOutlined, UndoOutlined, DeleteOutlined } from '@ant-design/icons';
import AppLayout from '../components/Layout';
import styles from './SmartOps.module.css';
import axios from 'axios';

interface Operation {
  id: string;
  type: string;
  description: string;
  status: 'pending' | 'success' | 'failed';
  timestamp: string;
  details: string;
}

interface OperationTemplate {
  id: number;
  name: string;
  description: string;
  operation_type: string;
  required_params: Record<string, string>;
}

const SmartOps: React.FC = () => {
  const [operations, setOperations] = useState<Operation[]>([]);
  const [templates, setTemplates] = useState<OperationTemplate[]>([]);
  const [loadingIds, setLoadingIds] = useState<Set<number>>(new Set());
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<OperationTemplate | null>(null);
  const [form] = Form.useForm();

  const API_BASE = import.meta.env.VITE_API_URL || '';

  // 获取操作模板
  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/operations/templates`);
      setTemplates(response.data);
    } catch (error: any) {
      message.error('获取操作模板失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 获取操作日志
  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/operations/logs`);
      const logs = response.data.items.map((log: any) => ({
        id: String(log.id),
        type: log.operation_type,
        description: `${log.operation_target} - ${log.status}`,
        status: log.status,
        timestamp: new Date(log.created_at).toLocaleString('zh-CN'),
        details: JSON.stringify(log.detail, null, 2),
      }));
      setOperations(logs);
    } catch (error: any) {
      message.error('获取操作日志失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 初始加载
  useEffect(() => {
    fetchTemplates();
    fetchLogs();
  }, []);

  // 执行操作
  const handleExecuteOperation = async (template: OperationTemplate) => {
    // 设置当前模板为 loading 状态
    setLoadingIds(prev => new Set(prev).add(template.id));

    try {
      const response = await axios.post(`${API_BASE}/api/operations/execute`, {
        operation_type: template.operation_type,
        parameters: {}, // 使用默认参数
      });

      if (response.data.status === 'success') {
        message.success(`操作执行成功: ${template.name}`);
      } else {
        message.error(`操作执行失败: ${response.data.error || '未知错误'}`);
      }

      // 刷新日志
      await fetchLogs();
    } catch (error: any) {
      message.error('执行操作失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      // 移除当前模板的 loading 状态
      setLoadingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(template.id);
        return newSet;
      });
    }
  };

  return (
    <AppLayout currentMenu="operations">
      <div className={styles.pageContainer}>
        <div className={styles.pageHeader}>
          <h1 className={styles.pageTitle}>⚙️ 智能操作</h1>
          <span className={styles.pageSubtitle}>AI自动执行业务操作，记录所有操作日志和回滚选项</span>
        </div>

        {/* 操作模板 */}
        <div className={styles.templateSection}>
          <h2 className={styles.sectionTitle}>操作模板</h2>
          <div className={styles.templateGrid}>
            {templates.map(template => (
              <Card key={template.id} className={styles.templateCard}>
                <div className={styles.templateIcon}>
                  {template.operation_type === 'approve_order' && '✅'}
                  {template.operation_type === 'export_users' && '📥'}
                  {template.operation_type === 'process_refund' && '💰'}
                  {template.operation_type === 'batch_update_stock' && '📦'}
                </div>
                <h3 className={styles.templateName}>{template.name}</h3>
                <p className={styles.templateDesc}>{template.description}</p>
                <Button
                  type="primary"
                  block
                  icon={<PlayCircleOutlined />}
                  loading={loadingIds.has(template.id)}
                  onClick={() => handleExecuteOperation(template)}
                >
                  执行
                </Button>
              </Card>
            ))}
          </div>
        </div>

        {/* 操作日志 */}
        <Card title="📋 操作日志" className={styles.logCard} style={{ marginTop: 32 }}>
          {operations.length === 0 ? (
            <Empty description="暂无操作记录" />
          ) : (
            <Timeline>
              {operations.map(op => (
                <Timeline.Item
                  key={op.id}
                  dot={
                    op.status === 'success' ? (
                      <span style={{ color: '#10b981' }}>✓</span>
                    ) : op.status === 'failed' ? (
                      <span style={{ color: '#ef4444' }}>✗</span>
                    ) : (
                      <span style={{ color: '#ffd700' }}>◌</span>
                    )
                  }
                >
                  <div className={styles.logItem}>
                    <div className={styles.logHeader}>
                      <span className={styles.logType}>{op.type}</span>
                      <Tag color={
                        op.status === 'success' ? 'green' : 
                        op.status === 'failed' ? 'red' : 'orange'
                      }>
                        {op.status === 'success' ? '成功' : 
                         op.status === 'failed' ? '失败' : '处理中'}
                      </Tag>
                    </div>
                    <p className={styles.logDesc}>{op.description}</p>
                    <p className={styles.logTime}>{op.timestamp}</p>
                    <Space>
                      <Button type="link" size="small" icon={<UndoOutlined />}>
                        回滚
                      </Button>
                      <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                        删除
                      </Button>
                    </Space>
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          )}
        </Card>
      </div>
    </AppLayout>
  );
};

export default SmartOps;
