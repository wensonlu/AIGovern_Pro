import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Tag, Modal, Form, Input, InputNumber, message, Timeline, Tooltip } from 'antd';
import { EditOutlined, HistoryOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons';
import AppLayout from '../components/Layout';
import axios from 'axios';
import styles from './Products.module.css';

interface Product {
  id: number;
  name: string;
  sku: string;
  price: number;
  stock: number;
  category: string;
  created_at: string;
}

interface PriceHistory {
  id: number;
  product_id: number;
  product_name: string;
  old_price: number;
  new_price: number;
  changed_by: string;
  changed_by_id: number;
  reason?: string;
  created_at: string;
}

const Products: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [historyVisible, setHistoryVisible] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [priceHistory, setPriceHistory] = useState<PriceHistory[]>([]);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 获取商品列表
  const API_BASE = import.meta.env.VITE_API_URL || '';

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/api/products`);
      setProducts(response.data);
    } catch (error: any) {
      message.error('获取商品列表失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 获取价格修改历史
  const fetchPriceHistory = async (productId: number) => {
    try {
      const response = await axios.get(`${API_BASE}/api/products/${productId}/price-history`);
      setPriceHistory(response.data);
    } catch (error: any) {
      message.error('获取价格历史失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 初始加载
  useEffect(() => {
    fetchProducts();
  }, []);

  // 打开价格历史弹窗
  const showPriceHistory = (product: Product) => {
    setSelectedProduct(product);
    fetchPriceHistory(product.id);
    setHistoryVisible(true);
  };

  // 打开编辑弹窗
  const showEditModal = (product: Product) => {
    setSelectedProduct(product);
    form.setFieldsValue({
      name: product.name,
      price: product.price,
      stock: product.stock,
      category: product.category,
    });
    setEditModalVisible(true);
  };

  // 保存商品修改
  const handleSave = async (values: any) => {
    if (!selectedProduct) return;

    try {
      await axios.put(`${API_BASE}/api/products/${selectedProduct.id}`, values);
      message.success('商品更新成功');
      setEditModalVisible(false);
      fetchProducts(); // 刷新列表
    } catch (error: any) {
      message.error('更新失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '商品名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'SKU',
      dataIndex: 'sku',
      key: 'sku',
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '库存',
      dataIndex: 'stock',
      key: 'stock',
      render: (stock: number) => (
        <Tag color={stock < 10 ? 'red' : stock < 50 ? 'orange' : 'green'}>
          {stock}
        </Tag>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => category || '未分类',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Product) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<EditOutlined />}
            onClick={() => showEditModal(record)}
          >
            编辑
          </Button>
          <Button
            size="small"
            icon={<HistoryOutlined />}
            onClick={() => showPriceHistory(record)}
          >
            价格历史
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <AppLayout currentMenu="products">
      <div className={styles.pageContainer}>
        <div className={styles.pageHeader}>
          <h1 className={styles.pageTitle}>🛍️ 商品管理</h1>
          <span className={styles.pageSubtitle}>管理商品信息、查看价格修改历史</span>
        </div>

        <Card className={styles.tableCard}>
          <Table
            dataSource={products}
            columns={columns}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        </Card>

        {/* 价格历史弹窗 */}
        <Modal
          title={`${selectedProduct?.name} - 价格修改历史`}
          open={historyVisible}
          onCancel={() => setHistoryVisible(false)}
          footer={null}
          width={700}
        >
          {priceHistory.length === 0 ? (
            <div className={styles.emptyHistory}>暂无价格修改记录</div>
          ) : (
            <Timeline mode="left" className={styles.historyTimeline}>
              {priceHistory.map((record) => (
                <Timeline.Item
                  key={record.id}
                  label={new Date(record.created_at).toLocaleString('zh-CN')}
                  dot={
                    record.changed_by === 'ai' ? (
                      <Tooltip title="AI助手修改">
                        <RobotOutlined style={{ color: '#00d9ff' }} />
                      </Tooltip>
                    ) : (
                      <Tooltip title="用户修改">
                        <UserOutlined style={{ color: '#52c41a' }} />
                      </Tooltip>
                    )
                  }
                >
                  <div className={styles.historyItem}>
                    <div className={styles.historyPrice}>
                      <span className={styles.oldPrice}>¥{record.old_price.toFixed(2)}</span>
                      <span className={styles.arrow}>→</span>
                      <span className={styles.newPrice}>¥{record.new_price.toFixed(2)}</span>
                    </div>
                    <div className={styles.historyInfo}>
                      <Tag color={record.changed_by === 'ai' ? 'blue' : 'green'}>
                        {record.changed_by === 'ai' ? '🤖 AI助手' : '👤 用户'}
                      </Tag>
                      {record.reason && (
                        <span className={styles.reason}>{record.reason}</span>
                      )}
                    </div>
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          )}
        </Modal>

        {/* 编辑商品弹窗 */}
        <Modal
          title="编辑商品"
          open={editModalVisible}
          onCancel={() => setEditModalVisible(false)}
          onOk={() => form.submit()}
        >
          <Form form={form} layout="vertical" onFinish={handleSave}>
            <Form.Item
              name="name"
              label="商品名称"
              rules={[{ required: true, message: '请输入商品名称' }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              name="price"
              label="价格"
              rules={[{ required: true, message: '请输入价格' }]}
            >
              <InputNumber
                min={0}
                precision={2}
                style={{ width: '100%' }}
                prefix="¥"
              />
            </Form.Item>
            <Form.Item
              name="stock"
              label="库存"
              rules={[{ required: true, message: '请输入库存' }]}
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="category" label="分类">
              <Input />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </AppLayout>
  );
};

export default Products;
