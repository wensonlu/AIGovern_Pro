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

interface ReasoningStep {
  title: string;
  detail: string;
  status: 'planned' | 'done' | 'skipped';
}

const AIAssistantDemo: React.FC = () => {
  const { message } = App.useApp();
  const [sessionId, setSessionId] = useState<string>('');
  const [timeline, setTimeline] = useState<AssistantTimelineItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [approvalLoading, setApprovalLoading] = useState(false);
  const [pendingToolCallId, setPendingToolCallId] = useState<string>('');
  const [approvalModalOpen, setApprovalModalOpen] = useState(false);

  const [question, setQuestion] = useState(
    '看下近30天销售趋势，如果连续两周下滑，给张三创建一个复盘任务。'
  );
  const [reportText, setReportText] = useState('');
  const [taskProposal, setTaskProposal] = useState('');
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);

  const latestSummary = useMemo(() => {
    if (!timeline.length) return '尚未执行';
    const latest = timeline[timeline.length - 1];
    return `${latest.tool_name} / ${latest.status}`;
  }, [timeline]);

  const shouldCreateTask = useMemo(() => {
    const q = question.toLowerCase();
    return ['任务', '复盘', '跟进', '创建', '安排'].some((kw) => q.includes(kw));
  }, [question]);

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

  const summarizeTrend = (rows: Array<Record<string, any>>) => {
    if (!rows.length) return { report: '未查询到有效数据。', isDownward: false };
    const values = rows.map((r) => Number(r.gmv || 0));
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const last7 = values.slice(-7);
    const prev7 = values.slice(-14, -7);
    const last7Avg = last7.reduce((a, b) => a + b, 0) / Math.max(last7.length, 1);
    const prev7Avg = prev7.reduce((a, b) => a + b, 0) / Math.max(prev7.length, 1);
    const isDownward = last7Avg < prev7Avg;
    const changePct = prev7Avg > 0 ? ((last7Avg - prev7Avg) / prev7Avg) * 100 : 0;

    const report = [
      `已分析近${rows.length}天销售额，日均 GMV 约 ${avg.toFixed(0)}。`,
      `最近7天均值 ${last7Avg.toFixed(0)}，前7天均值 ${prev7Avg.toFixed(0)}。`,
      `环比变化 ${changePct.toFixed(2)}%。`,
      isDownward ? '结论：近期呈下滑趋势，建议安排复盘。' : '结论：暂无明显下滑趋势，可持续观察。',
    ].join('\n');

    return { report, isDownward };
  };

  const runDemoFlow = async () => {
    setLoading(true);
    setReportText('');
    setTaskProposal('');
    setReasoningSteps([
      { title: '理解问题', detail: `解析你的问题：${question}`, status: 'done' },
      { title: '获取数据', detail: '调用 read_sql 获取近30天GMV趋势', status: 'planned' },
      { title: '生成图表', detail: '调用 generate_chart_data 组织可视化数据', status: 'planned' },
      {
        title: '行动决策',
        detail: shouldCreateTask ? '若趋势下滑则申请创建跟进任务' : '本次仅给出分析结论，不触发写操作',
        status: 'planned',
      },
    ]);

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

      setReasoningSteps((prev) => prev.map((s, idx) => (idx === 1 ? { ...s, status: 'done' } : s)));

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
      setReasoningSteps((prev) => prev.map((s, idx) => (idx === 2 ? { ...s, status: 'done' } : s)));

      const rows = (((readRes.data as Record<string, any>) || {}).rows || []) as Array<Record<string, any>>;
      const { report, isDownward } = summarizeTrend(rows);
      setReportText(report);

      if (shouldCreateTask && isDownward) {
        const dynamicTitle = question.includes('华东') ? '华东销售下滑复盘' : '销售趋势复盘';
        const followupRes = await callAssistantTool(
          sid,
          TENANT_ID,
          USER_ID,
          'create_followup_task',
          {
            title: dynamicTitle,
            assignee: '张三',
            due_date: '2026-05-16',
            priority: 'high',
            context: report,
          }
        );

        setTaskProposal(`拟创建任务：${dynamicTitle}（负责人：张三，截止：2026-05-16）`);

        if (!followupRes.ok && followupRes.status === 'pending_approval') {
          setPendingToolCallId(followupRes.tool_call_id);
          setApprovalModalOpen(true);
          message.warning('已进入审批，请确认是否创建任务');
        }
        setReasoningSteps((prev) => prev.map((s, idx) => (idx === 3 ? { ...s, status: 'done' } : s)));
      } else {
        setReasoningSteps((prev) => prev.map((s, idx) => (idx === 3 ? { ...s, status: 'skipped' } : s)));
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
      message.info('已拒绝执行任务创建');
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
                  message="输入任意业务问题，系统会展示计划、证据、结论与执行动作（可审批）"
                />

                <div className={styles.formGroup}>
                  <Text strong>你的问题</Text>
                  <Input.TextArea
                    rows={3}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="例如：看下近30天销售趋势，如果连续两周下滑就安排复盘"
                  />
                </div>

                <Space>
                  <Button type="primary" onClick={runDemoFlow} loading={loading}>
                    执行问题
                  </Button>
                  <Button
                    onClick={async () => {
                      if (!sessionId) {
                        message.info('暂无会话，请先执行问题');
                        return;
                      }
                      await refreshTimeline(sessionId);
                    }}
                  >
                    刷新时间线
                  </Button>
                </Space>

                <Divider />

                <Card size="small" title="推理摘要（可解释过程）" className={styles.reasoningCard}>
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    {reasoningSteps.map((step) => (
                      <div key={step.title} className={styles.reasoningRow}>
                        <Tag color={step.status === 'done' ? 'green' : step.status === 'skipped' ? 'default' : 'blue'}>
                          {step.status}
                        </Tag>
                        <Text strong>{step.title}</Text>
                        <Text type="secondary">{step.detail}</Text>
                      </div>
                    ))}
                  </Space>
                </Card>

                <Card size="small" title="复盘/分析内容" className={styles.reportCard}>
                  <Paragraph className={styles.reportText}>{reportText || '执行后将显示分析内容。'}</Paragraph>
                  {taskProposal && <Paragraph className={styles.reportText}><strong>{taskProposal}</strong></Paragraph>}
                </Card>

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
          <Text type="secondary">仅在问题明确需要行动且趋势下滑时触发。</Text>
          <Text type="secondary">tool_call_id: {pendingToolCallId}</Text>
        </Space>
      </Modal>
    </AppLayout>
  );
};

export default AIAssistantDemo;
