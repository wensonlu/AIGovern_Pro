import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { Button, Upload, Table, Tag, Space, Modal, Input, Card, Progress, Row, Col, Empty, Spin, Alert, Skeleton } from 'antd';
import { InboxOutlined, DeleteOutlined, EyeOutlined, CheckOutlined } from '@ant-design/icons';
import { UploadChangeParam, UploadFile } from 'antd/es/upload/interface';
import AppLayout from '../components/Layout';
import styles from './Documents.module.css';

const { TextArea } = Input;

// API 配置
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface DocumentItem {
  id: string;
  name: string;
  size: number;
  uploadTime: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  embeddingProgress: number;
  chunks: number;
  retrievalTest?: {
    testQuery: string;
    results: Array<{ content: string; score: number }>;
    answerQuality: 'high' | 'medium' | 'low';
  };
}

const Documents: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<DocumentItem[]>([
    {
      id: '1',
      name: '企业经营手册.pdf',
      size: 2048,
      uploadTime: '2026-03-10 14:30',
      status: 'completed',
      embeddingProgress: 100,
      chunks: 124,
    },
    {
      id: '2',
      name: '产品规格说明.docx',
      size: 1024,
      uploadTime: '2026-03-11 10:15',
      status: 'processing',
      embeddingProgress: 65,
      chunks: 48,
    },
    {
      id: '3',
      name: '销售规范.txt',
      size: 512,
      uploadTime: '2026-03-12 09:00',
      status: 'pending',
      embeddingProgress: 0,
      chunks: 0,
    },
  ]);

  const [testModalVisible, setTestModalVisible] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [testQuery, setTestQuery] = useState('');
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<DocumentItem['retrievalTest'] | null>(null);

  const handleUpload = (info: UploadChangeParam<UploadFile>) => {
    const file = info.file;
    if (file.status === 'done') {
      const newDoc: DocumentItem = {
        id: Date.now().toString(),
        name: file.name,
        size: (file.size as number) / 1024,
        uploadTime: new Date().toLocaleString('zh-CN'),
        status: 'pending',
        embeddingProgress: 0,
        chunks: 0,
      };
      setDocuments([...documents, newDoc]);

      // 模拟向量化过程
      setTimeout(() => {
        setDocuments(prev =>
          prev.map(doc =>
            doc.id === newDoc.id
              ? { ...doc, status: 'processing', embeddingProgress: 35 }
              : doc,
          ),
        );
      }, 1000);

      setTimeout(() => {
        setDocuments(prev =>
          prev.map(doc =>
            doc.id === newDoc.id
              ? { ...doc, status: 'processing', embeddingProgress: 70 }
              : doc,
          ),
        );
      }, 2000);

      setTimeout(() => {
        setDocuments(prev =>
          prev.map(doc =>
            doc.id === newDoc.id
              ? { ...doc, status: 'completed', embeddingProgress: 100, chunks: 56 }
              : doc,
          ),
        );
      }, 3500);
    }
  };

  const handleTestRetrieval = useCallback((doc: DocumentItem) => {
    setSelectedDoc(doc);
    setTestModalVisible(true);
    setTestQuery('');
    setTestResult(null);
  }, []);

  const runRetrievalTest = async () => {
    if (!testQuery.trim() || !selectedDoc) return;

    setTestLoading(true);

    // 模拟RAG检索过程
    setTimeout(() => {
      const mockResults = [
        {
          content: '根据企业经营手册第3章，员工招聘流程包括：1. 职位发布，2. 简历筛选，3. 笔试评估，4. 面试阶段，5. 合同签署。',
          score: 0.94,
        },
        {
          content: '人事部门负责招聘工作的组织和实施，确保招聘流程的公正性和透明度。',
          score: 0.82,
        },
        {
          content: '所有新员工需要进行为期3天的入职培训。',
          score: 0.71,
        },
      ];

      setTestResult({
        testQuery,
        results: mockResults,
        answerQuality: 'high',
      });

      setTestLoading(false);
    }, 1500);
  };

  const handleDeleteDocument = useCallback((id: string) => {
    Modal.confirm({
      title: '删除文档',
      content: '确认删除该文档？此操作不可撤销。',
      okText: '删除',
      cancelText: '取消',
      onOk() {
        setDocuments(prev => prev.filter(doc => doc.id !== id));
      },
    });
  }, []);

  const columns = useMemo(
    () => [
      {
        title: '文档名称',
        dataIndex: 'name',
        key: 'name',
        sorter: (a: DocumentItem, b: DocumentItem) => a.name.localeCompare(b.name),
        render: (text: string) => (
          <div className={styles.docName}>
            <span className={styles.docIcon}>📄</span>
            {text}
          </div>
        ),
      },
      {
        title: '文件大小',
        dataIndex: 'size',
        key: 'size',
        sorter: (a: DocumentItem, b: DocumentItem) => a.size - b.size,
        render: (size: number) => `${(size / 1024).toFixed(2)} MB`,
      },
      {
        title: '向量化进度',
        dataIndex: 'embeddingProgress',
        key: 'embeddingProgress',
        render: (progress: number, record: DocumentItem) => (
          <div className={styles.progressCell}>
            <Progress
              percent={progress}
              size="small"
              status={
                record.status === 'completed'
                  ? 'success'
                  : record.status === 'failed'
                    ? 'exception'
                    : 'active'
              }
              strokeColor={{
                '0%': '#7f5af0',
                '100%': '#00d9ff',
              }}
            />
            {record.chunks > 0 && (
              <span className={styles.chunkCount}>({record.chunks}个文段)</span>
            )}
          </div>
        ),
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        filters: [
          { text: '待处理', value: 'pending' },
          { text: '处理中', value: 'processing' },
          { text: '已完成', value: 'completed' },
          { text: '失败', value: 'failed' },
        ],
        onFilter: (value: boolean | React.Key, record: DocumentItem) =>
          record.status === value,
        render: (status: string) => {
          const statusConfig: Record<string, { color: string; text: string }> = {
            pending: { color: 'default', text: '待处理' },
            processing: { color: 'processing', text: '处理中' },
            completed: { color: 'success', text: '已完成' },
            failed: { color: 'error', text: '失败' },
          };
          return <Tag color={statusConfig[status]?.color}>{statusConfig[status]?.text}</Tag>;
        },
      },
      {
        title: '上传时间',
        dataIndex: 'uploadTime',
        key: 'uploadTime',
      },
      {
        title: '操作',
        key: 'action',
        render: (_: any, record: DocumentItem) => (
          <Space size="small">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => Modal.info({ title: record.name, content: '文档预览内容（此处展示摘要）' })}
            >
              预览
            </Button>
            {record.status === 'completed' && (
              <Button
                type="link"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => handleTestRetrieval(record)}
              >
                测试
              </Button>
            )}
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteDocument(record.id)}
            >
              删除
            </Button>
          </Space>
        ),
      },
    ],
    [handleDeleteDocument, handleTestRetrieval],
  );

  // Simulate initial loading
  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  // Loading skeleton
  if (loading) {
    return (
      <AppLayout currentMenu="documents">
        <div className={styles.pageContainer}>
          <Skeleton active paragraph={{ rows: 4 }} />
          <Skeleton active paragraph={{ rows: 8 }} style={{ marginTop: 24 }} />
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout currentMenu="documents">
      <div className={styles.pageContainer}>
        {/* 页面标题 */}
        <div className={styles.pageHeader}>
          <h1 className={styles.pageTitle}>📚 知识库管理</h1>
          <span className={styles.pageSubtitle}>上传、管理和测试知识库文档，验证RAG检索能力</span>
        </div>

        {/* 上传区域 */}
        <Card className={styles.uploadCard} bordered={false}>
          <div className={styles.uploadSection}>
            <Upload.Dragger
              name="file"
              action={`${API_BASE_URL}/api/documents/upload`}
              onChange={handleUpload}
              multiple
              accept=".pdf,.doc,.docx,.txt,.md"
              className={styles.uploader}
            >
              <p className={styles.uploadIcon}>
                <InboxOutlined style={{ fontSize: 48 }} />
              </p>
              <p className={styles.uploadText}>点击或拖拽文件到此区域上传</p>
              <p className={styles.uploadHint}>支持 PDF、Word、TXT、Markdown 格式，最大50MB</p>
            </Upload.Dragger>

            <Alert
              type="info"
              message="💡 提示：上传的文档将自动分块、向量化并存入Milvus向量库，以支持RAG检索"
              className={styles.uploadAlert}
              showIcon
            />
          </div>
        </Card>

        {/* 文档统计 */}
        <Row gutter={[24, 24]} style={{ marginTop: 32, marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card className={styles.statCard} bordered={false}>
              <div className={styles.statLabel}>总文档数</div>
              <div className={styles.statValue}>{documents.length}</div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card className={styles.statCard} bordered={false}>
              <div className={styles.statLabel}>已完成</div>
              <div className={styles.statValue}>
                {documents.filter(d => d.status === 'completed').length}
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card className={styles.statCard} bordered={false}>
              <div className={styles.statLabel}>处理中</div>
              <div className={styles.statValue}>
                {documents.filter(d => d.status === 'processing').length}
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card className={styles.statCard} bordered={false}>
              <div className={styles.statLabel}>总文段数</div>
              <div className={styles.statValue}>
                {documents.reduce((sum, doc) => sum + doc.chunks, 0)}
              </div>
            </Card>
          </Col>
        </Row>

        {/* 文档列表 */}
        <Card className={styles.tableCard} bordered={false} title="文档列表">
          {documents.length === 0 ? (
            <Empty description="还没有上传任何文档" />
          ) : (
            <Table
              dataSource={documents}
              columns={columns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              className={styles.table}
            />
          )}
        </Card>
      </div>

      {/* 检索测试模态框 */}
      <Modal
        title={`📝 检索测试 - ${selectedDoc?.name}`}
        open={testModalVisible}
        onCancel={() => setTestModalVisible(false)}
        footer={null}
        width={700}
        className={styles.testModal}
      >
        <Spin spinning={testLoading} tip="正在执行检索...">
          {/* 输入测试查询 */}
          <div className={styles.testInputSection}>
            <label className={styles.testLabel}>输入测试问题</label>
            <TextArea
              placeholder="例如：这个文档主要讲了什么内容？"
              rows={3}
              value={testQuery}
              onChange={e => setTestQuery(e.target.value)}
              disabled={testLoading}
            />
            <Button
              type="primary"
              onClick={runRetrievalTest}
              loading={testLoading}
              disabled={!testQuery.trim()}
              style={{ marginTop: 16 }}
            >
              执行检索
            </Button>
          </div>

          {/* 检索结果 */}
          {testResult && (
            <div className={styles.testResultSection}>
              <div className={styles.testResultHeader}>
                <span className={styles.testResultTitle}>检索结果</span>
                <Tag color={testResult.answerQuality === 'high' ? 'green' : 'orange'}>
                  质量: {testResult.answerQuality === 'high' ? '优秀' : '一般'}
                </Tag>
              </div>

              <div className={styles.resultsList}>
                {testResult.results.map((result, idx) => (
                  <div key={idx} className={styles.resultItem}>
                    <div className={styles.resultRank}>#{idx + 1}</div>
                    <div className={styles.resultContent}>
                      <p className={styles.resultText}>{result.content}</p>
                      <div className={styles.resultScore}>
                        <span>相关度：</span>
                        <Progress
                          type="circle"
                          percent={Math.round(result.score * 100)}
                          width={40}
                          strokeColor={{
                            '0%': '#7f5af0',
                            '100%': '#00d9ff',
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <Alert
                type="success"
                message="✅ 检索成功！文档已正确向量化，可用于RAG问答"
                style={{ marginTop: 16 }}
                showIcon
              />
            </div>
          )}
        </Spin>
      </Modal>
    </AppLayout>
  );
};

export default Documents;
