import React from 'react';
import { Card, Row, Col, Statistic, Alert, Space, Tag, Button, Empty } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import AppLayout from '../components/Layout';
import styles from './Diagnosis.module.css';

const Diagnosis: React.FC = () => {
  const diagnosticReports = [
    {
      category: '订单指标',
      icon: '📦',
      metrics: [
        { label: '日均订单', value: '8,934', change: -23, status: 'warning' },
        { label: '订单金额', value: '¥847K', change: -18, status: 'warning' },
      ],
      analysis: '订单量环比下降23%，主要原因为：1) 竞品促销活动，2) 季节性下滑',
      suggestion: '建议采取应对措施：调整价格、增加促销力度',
    },
    {
      category: '转化指标',
      icon: '📈',
      metrics: [
        { label: '转化率', value: '3.24%', change: -5, status: 'warning' },
        { label: '客单价', value: '¥450', change: 8, status: 'success' },
      ],
      analysis: '转化率下降，可能受到流量质量下降的影响',
      suggestion: '优化着陆页、提升商品质量展示',
    },
    {
      category: '客户指标',
      icon: '👥',
      metrics: [
        { label: '活跃用户', value: '2,384', change: 12, status: 'success' },
        { label: '流失用户', value: '234', change: 45, status: 'danger' },
      ],
      analysis: '虽然活跃用户增加，但流失率显著上升，需要关注客户保留',
      suggestion: '推出会员权益计划，提升客户粘性',
    },
  ];

  return (
    <AppLayout currentMenu="diagnosis">
      <div className={styles.pageContainer}>
        <div className={styles.pageHeader}>
          <h1 className={styles.pageTitle}>🔬 经营诊断</h1>
          <span className={styles.pageSubtitle}>核心指标监控、异常识别、根因分析与决策建议</span>
        </div>

        {/* 总体诊断预警 */}
        <Alert
          message="⚠️ 经营预警：近期业务指标下行，需要重点关注"
          type="warning"
          showIcon
          style={{ marginBottom: 24 }}
        />

        {/* 诊断报告卡片 */}
        {diagnosticReports.map((report, idx) => (
          <Card
            key={idx}
            title={`${report.icon} ${report.category}`}
            className={styles.reportCard}
            style={{ marginBottom: 24 }}
          >
            {/* 指标展示 */}
            <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
              {report.metrics.map((metric, i) => (
                <Col key={i} xs={24} sm={12} lg={6}>
                  <Statistic
                    title={metric.label}
                    value={metric.value}
                    prefix={
                      metric.change >= 0 ? (
                        <ArrowUpOutlined
                          style={{
                            color: metric.status === 'success' ? '#10b981' : '#ef4444',
                          }}
                        />
                      ) : (
                        <ArrowDownOutlined
                          style={{
                            color: metric.status === 'danger' ? '#ef4444' : '#ffd700',
                          }}
                        />
                      )
                    }
                    suffix={`${metric.change >= 0 ? '+' : ''}${metric.change}%`}
                  />
                </Col>
              ))}
            </Row>

            {/* 分析和建议 */}
            <div className={styles.analysis}>
              <div className={styles.analysisItem}>
                <h4 className={styles.analysisTitle}>🔍 根因分析</h4>
                <p className={styles.analysisText}>{report.analysis}</p>
              </div>
              <div className={styles.analysisItem}>
                <h4 className={styles.analysisTitle}>💡 优化建议</h4>
                <p className={styles.analysisText}>{report.suggestion}</p>
              </div>
            </div>

            <Space>
              <Button type="primary">查看详情</Button>
              <Button>导出报告</Button>
            </Space>
          </Card>
        ))}

        {/* 智能建议 */}
        <Card title="🤖 AI决策建议" className={styles.aiCard}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Alert
              message="基于多维数据分析，AI建议优先采取以下行动"
              type="info"
              showIcon
            />
            <ol>
              <li>立即启动&quot;顾客回归&quot;促销活动，目标恢复订单量20%</li>
              <li>优化商详页，提升转化率至3.5%+</li>
              <li>推出会员权益计划，降低客户流失率</li>
            </ol>
          </Space>
        </Card>
      </div>
    </AppLayout>
  );
};

export default Diagnosis;
