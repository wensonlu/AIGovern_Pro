import React, { useMemo, useRef, useState, useEffect } from 'react';
import { Button, Card, Col, Input, Row, Space, Statistic, Tag } from 'antd';
import {
  AimOutlined,
  BranchesOutlined,
  CheckCircleOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import {
  createProject,
  findForTask,
  recommendNext,
  updateProjectState,
  type SkillGraph,
  type SkillNode,
} from '@agent-skills-dashboard/core';
import { ProjectTracker, SkillCard, SkillMap } from '@agent-skills-dashboard/react';
import '@agent-skills-dashboard/react/styles';
import AppLayout from '../components/Layout';
import styles from './AgentSkills.module.css';

const SKILL_GRAPH: SkillGraph = {
  nodes: [
    {
      id: 'enterprise-scenario-modeling',
      name: '企业场景建模',
      description: '梳理岗位、业务对象、权限边界和高频决策场景，为后续智能能力确定清晰业务语境。',
      phase: 'define',
      triggers: ['新增业务域', '梳理核心用户旅程', '定义 AI-native 管理场景'],
      triggersStyle: 'auto',
      dependsOn: [],
      relatedSkills: ['rag-knowledge-design', 'governance-risk-review'],
      keywords: ['scenario', 'domain', 'enterprise', '业务', '场景', '权限'],
      filePath: 'skills/enterprise-scenario-modeling/SKILL.md',
    },
    {
      id: 'rag-knowledge-design',
      name: 'RAG 知识体系设计',
      description: '规划文档入库、切分、向量召回和引用呈现，让知识问答具备可追溯、可治理的基础。',
      phase: 'plan',
      triggers: ['接入企业文档', '优化知识问答', '需要引用来源'],
      triggersStyle: 'auto',
      dependsOn: ['enterprise-scenario-modeling'],
      relatedSkills: ['diagnostic-metric-system'],
      keywords: ['rag', 'knowledge', 'document', 'vector', '知识库', '文档', '召回'],
      filePath: 'skills/rag-knowledge-design/SKILL.md',
    },
    {
      id: 'sql-query-guardrails',
      name: 'SQL 生成护栏',
      description: '设计自然语言转 SQL 的 schema 约束、只读校验、结果解释和异常兜底，降低数据查询风险。',
      phase: 'plan',
      triggers: ['新增数据查询能力', '连接业务数据库', '限制 SQL 权限'],
      triggersStyle: 'auto',
      dependsOn: ['enterprise-scenario-modeling'],
      relatedSkills: ['diagnostic-metric-system'],
      keywords: ['sql', 'query', 'database', 'schema', '数据查询', '数据库'],
      filePath: 'skills/sql-query-guardrails/SKILL.md',
    },
    {
      id: 'operation-template-orchestration',
      name: '操作模板编排',
      description: '把审批、导出、补货、退款等操作沉淀为可审计模板，支持参数校验、执行记录和回滚入口。',
      phase: 'build',
      triggers: ['新增智能操作', '自动执行业务动作', '需要操作审计'],
      triggersStyle: 'auto',
      dependsOn: ['sql-query-guardrails'],
      relatedSkills: ['governance-risk-review'],
      keywords: ['operation', 'automation', 'template', 'rollback', '智能操作', '自动执行'],
      filePath: 'skills/operation-template-orchestration/SKILL.md',
    },
    {
      id: 'diagnostic-metric-system',
      name: '经营诊断指标体系',
      description: '把 KPI、异常检测、归因分析和推荐动作组织成可复用诊断框架，支撑业务诊断页面。',
      phase: 'build',
      triggers: ['设计诊断看板', '新增 KPI 指标', '分析经营异常'],
      triggersStyle: 'auto',
      dependsOn: ['rag-knowledge-design', 'sql-query-guardrails'],
      relatedSkills: ['visual-acceptance-loop'],
      keywords: ['diagnosis', 'analytics', 'kpi', 'metric', '经营诊断', '指标', '异常'],
      filePath: 'skills/diagnostic-metric-system/SKILL.md',
    },
    {
      id: 'agui-copilot-integration',
      name: 'AGUI 助手集成',
      description: '把聊天面板与知识问答、数据查询、操作执行串联起来，形成可解释的人机协作入口。',
      phase: 'build',
      triggers: ['扩展 ChatPanel', '接入多工具调用', '需要上下文助手'],
      triggersStyle: 'auto',
      dependsOn: ['rag-knowledge-design', 'operation-template-orchestration'],
      relatedSkills: ['visual-acceptance-loop'],
      keywords: ['agui', 'chat', 'copilot', 'tool', '助手', '聊天', '工具调用'],
      filePath: 'skills/agui-copilot-integration/SKILL.md',
    },
    {
      id: 'visual-acceptance-loop',
      name: '可视化验收闭环',
      description: '用构建、类型检查和浏览器走查验证页面状态，确保数据、交互、响应式布局可用。',
      phase: 'verify',
      triggers: ['前端页面变更', '需要可视化检查', '准备交付演示'],
      triggersStyle: 'auto',
      dependsOn: ['diagnostic-metric-system', 'agui-copilot-integration'],
      relatedSkills: ['governance-risk-review'],
      keywords: ['visual', 'browser', 'acceptance', 'frontend', '验收', '页面'],
      filePath: 'skills/visual-acceptance-loop/SKILL.md',
    },
    {
      id: 'governance-risk-review',
      name: '治理风险评审',
      description: '从权限、审计、提示词注入、数据泄露和回滚路径评审 AI 管理系统的上线风险。',
      phase: 'review',
      triggers: ['准备合并发布', '检查安全风险', '评审自动执行能力'],
      triggersStyle: 'auto',
      dependsOn: ['visual-acceptance-loop'],
      relatedSkills: ['release-readiness'],
      keywords: ['governance', 'risk', 'security', 'audit', '治理', '风险', '审计'],
      filePath: 'skills/governance-risk-review/SKILL.md',
    },
    {
      id: 'release-readiness',
      name: '发布准备清单',
      description: '确认环境变量、数据库迁移、回滚策略、监控指标和演示路径，降低上线不确定性。',
      phase: 'ship',
      triggers: ['准备上线', '部署到生产', '需要发布清单'],
      triggersStyle: 'auto',
      dependsOn: ['governance-risk-review'],
      relatedSkills: [],
      keywords: ['release', 'deploy', 'launch', 'env', '发布', '部署', '上线'],
      filePath: 'skills/release-readiness/SKILL.md',
    },
  ],
  edges: [
    { from: 'enterprise-scenario-modeling', to: 'rag-knowledge-design', type: 'depends' },
    { from: 'enterprise-scenario-modeling', to: 'sql-query-guardrails', type: 'depends' },
    { from: 'rag-knowledge-design', to: 'diagnostic-metric-system', type: 'depends' },
    { from: 'sql-query-guardrails', to: 'operation-template-orchestration', type: 'depends' },
    { from: 'sql-query-guardrails', to: 'diagnostic-metric-system', type: 'depends' },
    { from: 'rag-knowledge-design', to: 'agui-copilot-integration', type: 'depends' },
    { from: 'operation-template-orchestration', to: 'agui-copilot-integration', type: 'depends' },
    { from: 'diagnostic-metric-system', to: 'visual-acceptance-loop', type: 'depends' },
    { from: 'agui-copilot-integration', to: 'visual-acceptance-loop', type: 'depends' },
    { from: 'visual-acceptance-loop', to: 'governance-risk-review', type: 'depends' },
    { from: 'governance-risk-review', to: 'release-readiness', type: 'depends' },
    { from: 'operation-template-orchestration', to: 'governance-risk-review', type: 'relates' },
  ],
};

const initialTask = '需要为知识库、数据查询、智能操作和经营诊断规划下一步开发';

const AgentSkills: React.FC = () => {
  const graphPanelRef = useRef<HTMLDivElement>(null);
  const [graphWidth, setGraphWidth] = useState(820);
  const [project, setProject] = useState(() => createProject('AIGovern Pro Phase 2'));
  const [selectedSkill, setSelectedSkill] = useState<SkillNode | null>(SKILL_GRAPH.nodes[0]);
  const [task, setTask] = useState(initialTask);

  useEffect(() => {
    const element = graphPanelRef.current;
    if (!element) return;

    const updateWidth = () => {
      setGraphWidth(Math.max(520, Math.min(920, element.clientWidth - 48)));
    };

    updateWidth();
    const observer = new ResizeObserver(updateWidth);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const taskMatches = useMemo(() => findForTask(SKILL_GRAPH, task).slice(0, 6), [task]);
  const recommendations = useMemo(
    () => recommendNext(SKILL_GRAPH, project.currentPhase, task).slice(0, 3),
    [project.currentPhase, task]
  );

  const completedCount = project.completedSkills.length;
  const progressPercent = Math.round((completedCount / SKILL_GRAPH.nodes.length) * 100);

  const handleSkillComplete = (skillId: string) => {
    const skill = SKILL_GRAPH.nodes.find(item => item.id === skillId);
    if (!skill) return;

    setSelectedSkill(skill);
    setProject(current => {
      if (current.completedSkills.includes(skillId)) return current;
      return updateProjectState(current, skillId, SKILL_GRAPH);
    });
  };

  return (
    <AppLayout currentMenu="skills">
      <div className={styles.pageContainer}>
        <div className={styles.pageHeader}>
          <div>
            <h1 className={styles.pageTitle}>Agent Skills 可视化</h1>
            <span className={styles.pageSubtitle}>用技能图谱、阶段追踪和任务推荐管理 AI 原生交付流程</span>
          </div>
          <Tag color="cyan" className={styles.packageTag}>
            @agent-skills-dashboard/core + react
          </Tag>
        </div>

        <Row gutter={[16, 16]} className={styles.metricsRow}>
          <Col xs={12} md={6}>
            <Card className={styles.metricCard}>
              <Statistic title="Skills" value={SKILL_GRAPH.nodes.length} prefix={<AimOutlined />} />
            </Card>
          </Col>
          <Col xs={12} md={6}>
            <Card className={styles.metricCard}>
              <Statistic title="Links" value={SKILL_GRAPH.edges.length} prefix={<BranchesOutlined />} />
            </Card>
          </Col>
          <Col xs={12} md={6}>
            <Card className={styles.metricCard}>
              <Statistic title="Progress" value={progressPercent} suffix="%" prefix={<CheckCircleOutlined />} />
            </Card>
          </Col>
          <Col xs={12} md={6}>
            <Card className={styles.metricCard}>
              <Statistic title="Phase" value={project.currentPhase.toUpperCase()} prefix={<ThunderboltOutlined />} />
            </Card>
          </Col>
        </Row>

        <div className={styles.workspaceGrid}>
          <Card className={styles.graphCard} bordered={false}>
            <div className={styles.cardHeader}>
              <div>
                <h2>技能依赖图</h2>
                <p>点击节点查看详情，拖拽节点可以观察依赖关系。</p>
              </div>
            </div>
            <div ref={graphPanelRef} className={styles.graphCanvas}>
              <SkillMap
                graph={SKILL_GRAPH}
                currentPhase={project.currentPhase}
                width={graphWidth}
                height={520}
                onSkillClick={setSelectedSkill}
              />
            </div>
          </Card>

          <aside className={styles.sidePanel}>
            <Card className={styles.controlCard} bordered={false}>
              <Space direction="vertical" size={16} className={styles.fullWidth}>
                <div className={styles.cardHeader}>
                  <div>
                    <h2>当前任务</h2>
                    <p>核心包会基于任务文本匹配技能并推荐下一步。</p>
                  </div>
                </div>
                <Input.TextArea
                  value={task}
                  onChange={event => setTask(event.target.value)}
                  rows={5}
                  placeholder="输入当前开发任务、评审目标或上线场景"
                />
              </Space>
            </Card>

            <Card className={styles.controlCard} bordered={false}>
              <div className={styles.cardHeader}>
                <div>
                  <h2>下一步推荐</h2>
                  <p>结合当前阶段和任务上下文生成。</p>
                </div>
              </div>
              <Space direction="vertical" size={10} className={styles.fullWidth}>
                {recommendations.map(item => (
                  <Button
                    key={item.skill.id}
                    type="default"
                    className={styles.recommendButton}
                    onClick={() => setSelectedSkill(item.skill)}
                  >
                    <strong>{item.skill.name}</strong>
                    <span>{item.reason}</span>
                  </Button>
                ))}
              </Space>
            </Card>

            <Card className={styles.controlCard} bordered={false}>
              <div className={styles.cardHeader}>
                <div>
                  <h2>任务匹配</h2>
                  <p>按关键词、名称和描述筛选相关技能。</p>
                </div>
              </div>
              <div className={styles.matchList}>
                {taskMatches.map(skill => (
                  <button key={skill.id} type="button" onClick={() => setSelectedSkill(skill)}>
                    {skill.name}
                  </button>
                ))}
              </div>
            </Card>
          </aside>
        </div>

        <Card className={styles.trackerCard} bordered={false}>
          <ProjectTracker project={project} graph={SKILL_GRAPH} onSkillComplete={handleSkillComplete} />
        </Card>

        <SkillCard skill={selectedSkill} onClose={() => setSelectedSkill(null)} />
      </div>
    </AppLayout>
  );
};

export default AgentSkills;
