import React, { useMemo, useState } from 'react';
import {
  Alert,
  App,
  Button,
  Card,
  Divider,
  Input,
  Modal,
  Space,
  Spin,
  Tag,
  Timeline,
  Typography,
} from 'antd';
import AppLayout from '../components/Layout';
import {
  approveAssistantToolCall,
  AssistantTimelineItem,
  callAssistantTool,
  createAssistantSession,
  getAssistantTimeline,
  rejectAssistantToolCall,
} from '../services/api';
import styles from './AIAssistantDemo.module.css';

const { Text, Paragraph } = Typography;

const TENANT_ID = 'demo_tenant';
const USER_ID = 'demo_user';

const statusColorMap: Record<string, string> = {
  succeeded: 'green',
  failed: 'red',
  pending_approval: 'orange',
  rejected: 'volcano',
  approved: 'blue',
  executing: 'processing',
  draft: 'default',
};

const AIAssistantDemo: React.FC = () => {
  const { message } = App.useApp();
  const [sessionId, setSessionId] = useState<string>('');
  const [timeline, setTimeline] = useState<AssistantTimelineItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [approvalLoading, setApprovalLoading] = useState(false);
  const [pendingToolCallId, setPendingToolCallId] = useState<string>('');
  const [approvalModalOpen, setApprovalModalOpen] = useState(false);
  const [approvalNote, setApprovalNote] = useState('最近两周下滑，建议立即复盘');

  const latestSummary = useMemo(() => {
    if (!timeline.length) return '尚未执行';
    const latest = timeline[timeline.length - 1];
    return `${latest.tool_name} / ${latest.status}`;
  }, [timeline]);

  const ensureSession = async (): Promise<string> => {
    if (sessionId) return sessionId;
    const created = await createAssistantSession(TENANT_ID, USER_ID);
    setSessionId(created.session_id);
    return created.session_id;
  };

  const refreshTimeline = async (targetSessionId: string) => {
    const response = await getAssistantTimeline(targetSessionId);
    setTimeline(response.items || []);
  };

  const runDemoFlow = async () => {
    setLoading(true);
    try {
      const sid = await ensureSession();

      const readRes = await callAssistantTool(
        sid,
        TENANT_ID,
        USER_ID,
        'read_sql',
        {
          query: 'SELECT DATE(created_at) as date, SUM(amount) as gmv FROM orders GROUP BY DATE(created_at) ORDER BY date',
          limit: 30,
        }
      );

      if (!readRes.ok) {
        message.error(readRes.error_message || 'read_sql 执行失败');
        await refreshTimeline(sid);
        return;
      }

      await callAssistantTool(
        sid,
        TENANT_ID,
        USER_ID,
        'generate_chart_data',
        {
          source_tool_call_id: readRes.tool_call_id,
          chart_type: 'line',
          x_field: 'date',
          y_field: 'gmv',
        }
      );

      const followupRes = await callAssistantTool(
        sid,
        TENANT_ID,
        USER_ID,
        'create_followup_task',
        {
          title: '本周销售复盘',
          assignee: '张三',
          due_date: '2026-05-16',
          priority: 'high',
          context: approvalNote,
        }
      );

      if (!followupRes.ok && followupRes.status === 'pending_approval') {
        setPendingToolCallId(followupRes.tool_call_id);
        setApprovalModalOpen(true);
        message.warning('已进入审批，确认后将自动创建跟进任务');
      }

      await refreshTimeline(sid);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '执行失败');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!pendingToolCallId || !sessionId) return;
    setApprovalLoading(true);
    try {
      await approveAssistantToolCall(pendingToolCallId, 'manager_1');
      message.success('审批通过，已创建跟进任务');
      setApprovalModalOpen(false);
      await refreshTimeline(sessionId);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '审批失败');
    } finally {
      setApprovalLoading(false);
    }
  };

  const handleReject = async () => {
    if (!pendingToolCallId || !sessionId) return;
    setApprovalLoading(true);
    try {
      await rejectAssistantToolCall(pendingToolCallId, 'manager_1');
      message.info('已拒绝执行跟进任务');
      setApprovalModalOpen(false);
      await refreshTimeline(sessionId);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '拒绝失败');
    } finally {
      setApprovalLoading(false);
    }
  };

  return (
    <AppLayout currentMenu="ai-demo">
      <div className={styles.content}>
        <div className={styles.container}>
          <section className={styles.mainArea}>
            <Card title="AI 助手执行演示" className={styles.formCard}>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Alert
                  type="info"
                  showIcon
                  message="一键演示：read_sql -> generate_chart_data -> create_followup_task（审批）"
                />

                <div className={styles.formGroup}>
                  <Text strong>任务上下文备注</Text>
                  <Input.TextArea
                    rows={3}
                    value={approvalNote}
                    onChange={(e) => setApprovalNote(e.target.value)}
                    placeholder="输入这次创建跟进任务的上下文"
                  />
                </div>

                <Space>
                  <Button type="primary" onClick={runDemoFlow} loading={loading}>
                    执行完整演示
                  </Button>
                  <Button
                    onClick={async () => {
                      if (!sessionId) {
                        message.info('暂无会话，请先执行演示');
                        return;
                      }
                      await refreshTimeline(sessionId);
                    }}
                  >
                    刷新时间线
                  </Button>
                </Space>

                <Divider />
                <div className={styles.status}>
                  <Tag color="blue">Demo Status</Tag>
                  <div className={styles.statusContent}>
                    <p><strong>Tenant:</strong> {TENANT_ID}</p>
                    <p><strong>User:</strong> {USER_ID}</p>
                    <p><strong>Session:</strong> {sessionId || '未创建'}</p>
                    <p><strong>Latest:</strong> {latestSummary}</p>
                  </div>
                </div>
              </Space>
            </Card>
          </section>

          <aside className={styles.consolePanel}>
            <Card title="执行时间线" className={styles.timelineCard}>
              {loading && !timeline.length ? (
                <div className={styles.timelineLoading}><Spin /></div>
              ) : (
                <Timeline mode="left">
                  {timeline.map((item) => (
                    <Timeline.Item
                      key={item.tool_call_id}
                      color={statusColorMap[item.status] || 'gray'}
                      label={new Date(item.created_at).toLocaleTimeString()}
                    >
                      <div className={styles.timelineItemHeader}>
                        <Text strong>{item.tool_name}</Text>
                        <Tag color={statusColorMap[item.status] || 'default'}>{item.status}</Tag>
                      </div>
                      <Paragraph className={styles.timelineText}>入参: {item.input_summary}</Paragraph>
                      {item.output_summary && <Paragraph className={styles.timelineText}>结果: {item.output_summary}</Paragraph>}
                      <Space size="small">
                        {typeof item.latency_ms === 'number' && <Text type="secondary">{item.latency_ms} ms</Text>}
                        {item.error_code && <Tag color="red">{item.error_code}</Tag>}
                      </Space>
                    </Timeline.Item>
                  ))}
                </Timeline>
              )}
            </Card>
          </aside>
        </div>
      </div>

      <Modal
        open={approvalModalOpen}
        title="审批确认"
        okText="批准执行"
        cancelText="拒绝执行"
        onOk={handleApprove}
        onCancel={handleReject}
        confirmLoading={approvalLoading}
        closable={!approvalLoading}
        maskClosable={false}
      >
        <Space direction="vertical" size="small">
          <Text>检测到写操作：`create_followup_task`</Text>
          <Text type="secondary">将为“张三”创建“本周销售复盘”跟进任务。</Text>
          <Text type="secondary">tool_call_id: {pendingToolCallId}</Text>
        </Space>
      </Modal>
    </AppLayout>
  );
};

export default AIAssistantDemo;
