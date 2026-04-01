import React, { useState, useMemo, useEffect } from 'react';
import { Card, Row, Col, Space, Button, Skeleton } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import AppLayout from '../components/Layout';
import styles from './Dashboard.module.css';

// KPI Card data interface
interface KPIItem {
  label: string;
  value: string | number;
  change: string;
  trend: 'up' | 'down';
  icon: string;
}

// Memoized KPI Card component to prevent unnecessary re-renders
const KPICard: React.FC<{ kpi: KPIItem; idx: number }> = React.memo(({ kpi, idx }) => (
  <Col xs={24} sm={12} lg={6}>
    <div className={`${styles.kpiCard} ${styles[`kpi-${idx % 4}`]}`}>
      <div className={styles.kpiIcon}>{kpi.icon}</div>
      <div className={styles.kpiContent}>
        <div className={styles.kpiLabel}>{kpi.label}</div>
        <div className={styles.kpiValue}>{kpi.value}</div>
        <div className={`${styles.kpiChange} ${styles[kpi.trend]}`}>
          {kpi.trend === 'up' ? '📈' : '📉'} {kpi.change}
        </div>
      </div>
    </div>
  </Col>
));

KPICard.displayName = 'KPICard';

// Mock数据
const KPI_DATA: KPIItem[] = [
  { label: '订单数', value: 12458, change: '+12.5%', trend: 'up', icon: '📦' },
  { label: 'GMV', value: '¥2,847,392', change: '+8.3%', trend: 'up', icon: '💰' },
  { label: '转化率', value: '3.24%', change: '-0.5%', trend: 'down', icon: '📈' },
  { label: '活跃用户', value: 8934, change: '+5.2%', trend: 'up', icon: '👥' },
];

const CHART_DATA = [
  { date: '3/7', orders: 2400, revenue: 2210, users: 1890 },
  { date: '3/8', orders: 1398, revenue: 2290, users: 1200 },
  { date: '3/9', orders: 9800, revenue: 2000, users: 2210 },
  { date: '3/10', orders: 3908, revenue: 2108, users: 1890 },
  { date: '3/11', orders: 4800, revenue: 2176, users: 1200 },
  { date: '3/12', orders: 3800, revenue: 2100, users: 2210 },
  { date: '3/13', orders: 4300, revenue: 2300, users: 1200 },
];

const ANOMALY_DATA = [
  { id: 1, type: '订单异常', desc: '昨日订单环比下降23%', severity: 'high', action: '查看详情' },
  { id: 2, type: '库存预警', desc: '热销品SKU001库存不足', severity: 'medium', action: '补货' },
  { id: 3, type: '客户流失', desc: 'VIP用户H123年流失风险', severity: 'high', action: '干预' },
];

const RECOMMENDATIONS = [
  { id: 1, title: '订单下滑原因分析', desc: '根据诊断，最可能因素是竞品促销', action: '查看分析' },
  { id: 2, title: '库存优化建议', desc: '建议调整SKU001的进货数量', action: '执行' },
];

const CATEGORY_DATA = [
  { name: '电子产品', value: 35, fill: '#00D9FF' },
  { name: '服装配饰', value: 28, fill: '#FFD700' },
  { name: '家居用品', value: 22, fill: '#FF69B4' },
  { name: '食品饮料', value: 15, fill: '#7F5AF0' },
];

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);

  // Simulate initial loading
  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  // Memoize KPI cards rendering
  const kpiCards = useMemo(
    () =>
      KPI_DATA.map((kpi, idx) => (
        <KPICard key={`${kpi.label}-${idx}`} kpi={kpi} idx={idx} />
      )),
    []
  );

  return (
    <AppLayout currentMenu="dashboard">
      <div className={styles.pageContainer}>
        {/* 页面标题 */}
        <div className={styles.pageHeader}>
          <h1 className={styles.pageTitle}>仪表板</h1>
          <span className={styles.pageSubtitle}>实时企业经营数据监控中枢</span>
        </div>

        {loading ? (
          <Skeleton active paragraph={{ rows: 4 }} />
        ) : (
          <>
            {/* KPI卡片 */}
            <section className={styles.kpiSection}>
              <Row gutter={[24, 24]}>{kpiCards}</Row>
            </section>

            {/* 图表区域 */}
            <Row gutter={[24, 24]} style={{ marginTop: 32 }}>
              {/* 订单趋势 */}
              <Col xs={24} lg={16}>
                <Card className={styles.chartCard} title="订单趋势（7天）" bordered={false}>
                  <ResponsiveContainer width="100%" height={320}>
                    <LineChart data={CHART_DATA}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#404854" />
                      <XAxis dataKey="date" stroke="#909399" />
                      <YAxis stroke="#909399" />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: 8 }}
                        labelStyle={{ color: '#fff' }}
                      />
                      <Legend wrapperStyle={{ color: '#909399' }} />
                      <Line type="monotone" dataKey="orders" stroke="#00D9FF" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="revenue" stroke="#FFD700" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              </Col>

              {/* 分类占比 */}
              <Col xs={24} lg={8}>
                <Card className={styles.chartCard} title="销售分类占比" bordered={false}>
                  <ResponsiveContainer width="100%" height={320}>
                    <PieChart>
                      <Pie
                        data={CATEGORY_DATA}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {CATEGORY_DATA.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
            </Row>

            {/* 异常预警 + 推荐操作 */}
            <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
              {/* 异常预警 */}
              <Col xs={24} lg={12}>
                <Card className={styles.anomalyCard} title="⚠️ 异常预警" bordered={false}>
                  <Space direction="vertical" style={{ width: '100%' }} size="large">
                    {ANOMALY_DATA.map(item => (
                      <div key={item.id} className={`${styles.anomalyItem} ${styles[`severity-${item.severity}`]}`}>
                        <div className={styles.anomalyHeader}>
                          <span className={styles.anomalyType}>{item.type}</span>
                          <span className={`${styles.severityBadge} ${styles[`severity-${item.severity}`]}`}>
                            {item.severity === 'high' ? '高' : '中'}
                          </span>
                        </div>
                        <p className={styles.anomalyDesc}>{item.desc}</p>
                        <Button type="link" size="small" className={styles.anomalyAction}>
                          {item.action} →
                        </Button>
                      </div>
                    ))}
                  </Space>
                </Card>
              </Col>

              {/* 推荐操作 */}
              <Col xs={24} lg={12}>
                <Card className={styles.recommendCard} title="💡 AI推荐操作" bordered={false}>
                  <Space direction="vertical" style={{ width: '100%' }} size="large">
                    {RECOMMENDATIONS.map(rec => (
                      <div key={rec.id} className={styles.recommendItem}>
                        <div className={styles.recommendTitle}>{rec.title}</div>
                        <p className={styles.recommendDesc}>{rec.desc}</p>
                        <Button type="primary" size="small" className={styles.recommendAction}>
                          {rec.action}
                        </Button>
                      </div>
                    ))}
                  </Space>
                </Card>
              </Col>
            </Row>
          </>
        )}
      </div>
    </AppLayout>
  );
};

export default Dashboard;
