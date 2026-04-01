import React, { useState, useEffect } from 'react';
import { Input, Button, Card, Table, Empty, Space, Badge, Row, Col, Tag, Alert, message, Dropdown, Skeleton } from 'antd';
import { SendOutlined, CopyOutlined, DownloadOutlined, FileExcelOutlined, FileTextOutlined } from '@ant-design/icons';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import AppLayout from '../components/Layout';
import styles from './DataQuery.module.css';
import axios from 'axios';

const DataQuery: React.FC = () => {
  const [initialLoading, setInitialLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [generatedSql, setGeneratedSql] = useState('');
  const [chartType, setChartType] = useState('');

  // Simulate initial loading
  useEffect(() => {
    const timer = setTimeout(() => setInitialLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);



  const handleQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);

    try {
      // 调用后端真实 API
      const response = await axios.post('http://localhost:8000/api/query', {
        natural_language_query: query,
        context: {},
      });

      const data = response.data;
      setGeneratedSql(data.sql);
      setChartType(data.chart_type);
      setResults(data.result || []);
      message.success(`查询成功！返回 ${data.rows_count} 条数据，耗时 ${data.execution_time.toFixed(2)}s`);
    } catch (error: any) {
      message.error('查询失败: ' + (error.response?.data?.detail || error.message));
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // 导出数据为 CSV
  const exportToCSV = () => {
    if (results.length === 0) {
      message.warning('没有数据可导出');
      return;
    }

    // 获取表头
    const headers = Object.keys(results[0]);
    
    // 转换数据为 CSV 格式
    const csvContent = [
      headers.join(','), // 表头
      ...results.map(row => 
        headers.map(header => {
          const value = row[header];
          // 处理包含逗号或引号的值
          const stringValue = value === null || value === undefined ? '' : String(value);
          if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
            return `"${stringValue.replace(/"/g, '""')}"`;
          }
          return stringValue;
        }).join(',')
      )
    ].join('\n');

    // 创建下载链接
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = `query_result_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    message.success('CSV 文件导出成功！');
  };

  // 导出数据为 JSON
  const exportToJSON = () => {
    if (results.length === 0) {
      message.warning('没有数据可导出');
      return;
    }

    const jsonContent = JSON.stringify(results, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = `query_result_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    message.success('JSON 文件导出成功！');
  };

  // 导出菜单项
  const exportMenuItems = [
    {
      key: 'csv',
      icon: <FileExcelOutlined />,
      label: '导出为 CSV',
      onClick: exportToCSV,
    },
    {
      key: 'json',
      icon: <FileTextOutlined />,
      label: '导出为 JSON',
      onClick: exportToJSON,
    },
  ];

  // Loading skeleton
  if (initialLoading) {
    return (
      <AppLayout currentMenu="query">
        <div className={styles.pageContainer}>
          <Skeleton active paragraph={{ rows: 2 }} />
          <Skeleton active paragraph={{ rows: 4 }} style={{ marginTop: 24 }} />
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout currentMenu="query">
      <div className={styles.pageContainer}>
        <div className={styles.pageHeader}>
          <h1 className={styles.pageTitle}>🔍 数据查询</h1>
          <span className={styles.pageSubtitle}>自然语言转SQL，查询业务数据并生成可视化报表</span>
        </div>

        {/* 查询输入区 */}
        <Card className={styles.queryCard} bordered={false}>
          <div className={styles.queryInput}>
            <Input.TextArea
              placeholder="输入你的查询问题... 例如：过去7天的订单趋势如何？"
              rows={4}
              value={query}
              onChange={e => setQuery(e.target.value)}
              className={styles.textarea}
            />
            <Button
              type="primary"
              size="large"
              icon={<SendOutlined />}
              onClick={handleQuery}
              loading={loading}
              className={styles.queryBtn}
            >
              查询
            </Button>
          </div>
        </Card>

        {generatedSql && (
          <Card className={styles.sqlCard} title="生成的SQL语句" bordered={false} style={{ marginTop: 24 }}>
            <div className={styles.sqlPreview}>
              <code className={styles.sqlCode}>{generatedSql}</code>
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => navigator.clipboard.writeText(generatedSql)}
                style={{ marginTop: 12 }}
              >
                复制SQL
              </Button>
            </div>
          </Card>
        )}

        {results.length > 0 && (
          <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
            <Col xs={24} lg={16}>
              <Card className={styles.chartCard} title="数据可视化" bordered={false}>
                <ResponsiveContainer width="100%" height={300}>
                  {chartType === 'bar' ? (
                    <BarChart data={results}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#404854" />
                      <XAxis dataKey={Object.keys(results[0])[0]} stroke="#909399" />
                      <YAxis stroke="#909399" />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: 8 }}
                        labelStyle={{ color: '#fff' }}
                      />
                      <Bar dataKey={Object.keys(results[0])[1]} fill="#00D9FF" />
                    </BarChart>
                  ) : (
                    <LineChart data={results}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#404854" />
                      <XAxis dataKey={Object.keys(results[0])[0]} stroke="#909399" />
                      <YAxis stroke="#909399" />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: 8 }}
                        labelStyle={{ color: '#fff' }}
                      />
                      <Line type="monotone" dataKey={Object.keys(results[0])[1]} stroke="#00D9FF" strokeWidth={2} dot={false} />
                    </LineChart>
                  )}
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col xs={24} lg={8}>
              <Card className={styles.statsCard} title="数据统计" bordered={false}>
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <div className={styles.statItem}>
                    <span>总数据行数</span>
                    <span className={styles.statValue}>{results.length}</span>
                  </div>
                  <Dropdown menu={{ items: exportMenuItems }} placement="top" arrow>
                    <Button type="primary" block icon={<DownloadOutlined />}>
                      导出数据
                    </Button>
                  </Dropdown>
                </Space>
              </Card>
            </Col>
          </Row>
        )}

        {results.length > 0 && (
          <Card className={styles.tableCard} title="结果明细" bordered={false} style={{ marginTop: 24 }}>
            <Table
              dataSource={results}
              columns={results.length > 0 
                ? Object.keys(results[0]).map(key => ({ 
                    title: key, 
                    dataIndex: key, 
                    key,
                    ellipsis: true,
                  }))
                : []
              }
              rowKey={(record, index) => index?.toString() || '0'}
              pagination={{ pageSize: 10 }}
              className={styles.table}
              scroll={{ x: 'max-content' }}
            />
          </Card>
        )}

        {!loading && results.length === 0 && (
          <Empty description="等待查询" style={{ marginTop: 48 }} />
        )}
      </div>
    </AppLayout>
  );
};

export default DataQuery;
