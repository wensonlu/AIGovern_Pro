import React, { useState, useRef } from 'react';
import { Layout, Space, Button, Input, Spin, message, Card, Tag, Divider, Empty } from 'antd';
import { SendOutlined, BgColorsOutlined, BlockOutlined, FormOutlined } from '@ant-design/icons';
import AppLayout from '../components/Layout';
import MCPConsole from '../components/MCPConsole/MCPConsole';
import styles from './AIAssistantDemo.module.css';

const { Content } = Layout;

interface DemoElement {
  id: string;
  type: 'button' | 'input' | 'select' | 'form' | 'text';
  label: string;
  placeholder?: string;
  options?: Array<{ label: string; value: string }>;
}

const AIAssistantDemo: React.FC = () => {
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [demoFormData, setDemoFormData] = useState({
    productName: '',
    description: '',
    category: '',
    price: '',
    quantity: '',
  });

  const [showConsole, setShowConsole] = useState(true);

  const DEMO_ELEMENTS: DemoElement[] = [
    { id: 'product-name', type: 'input', label: 'Product Name', placeholder: 'Enter product name' },
    { id: 'description', type: 'input', label: 'Description', placeholder: 'Enter product description' },
    { id: 'category', type: 'select', label: 'Category', options: [
      { label: 'Electronics', value: 'electronics' },
      { label: 'Clothing', value: 'clothing' },
      { label: 'Books', value: 'books' },
      { label: 'Food', value: 'food' },
    ]},
    { id: 'price', type: 'input', label: 'Price', placeholder: 'Enter price' },
    { id: 'quantity', type: 'input', label: 'Quantity', placeholder: 'Enter quantity' },
  ];

  const handleInputChange = (field: string, value: string) => {
    setDemoFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = () => {
    if (Object.values(demoFormData).every(v => v)) {
      message.success('Form submitted successfully!');
      console.log('Form data:', demoFormData);
      setDemoFormData({
        productName: '',
        description: '',
        category: '',
        price: '',
        quantity: '',
      });
    } else {
      message.warning('Please fill all fields');
    }
  };

  const handleReset = () => {
    setDemoFormData({
      productName: '',
      description: '',
      category: '',
      price: '',
      quantity: '',
    });
    message.info('Form reset');
  };

  return (
    <AppLayout title="AI Assistant Demo">
      <Content className={styles.content}>
        <div className={styles.container}>
          {/* Main Content Area */}
          <div className={styles.mainArea}>
            <Card
              title="Interactive Demo Form"
              extra={
                <Space>
                  <Button type="primary" danger size="small" onClick={handleReset} data-testid="reset-btn">
                    Reset
                  </Button>
                </Space>
              }
              className={styles.formCard}
            >
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                {/* Product Name */}
                <div className={styles.formGroup}>
                  <label className={styles.label}>Product Name</label>
                  <Input
                    data-testid="product-name"
                    placeholder="Enter product name (e.g., Laptop, Phone, etc.)"
                    value={demoFormData.productName}
                    onChange={(e) => handleInputChange('productName', e.target.value)}
                    className={styles.input}
                  />
                </div>

                {/* Description */}
                <div className={styles.formGroup}>
                  <label className={styles.label}>Description</label>
                  <Input.TextArea
                    data-testid="description"
                    placeholder="Enter product description"
                    value={demoFormData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    rows={3}
                    className={styles.input}
                  />
                </div>

                {/* Category */}
                <div className={styles.formGroup}>
                  <label className={styles.label}>Category</label>
                  <select
                    data-testid="category"
                    value={demoFormData.category}
                    onChange={(e) => handleInputChange('category', e.target.value)}
                    className={styles.select}
                  >
                    <option value="">Select a category</option>
                    <option value="electronics">Electronics</option>
                    <option value="clothing">Clothing</option>
                    <option value="books">Books</option>
                    <option value="food">Food</option>
                  </select>
                </div>

                {/* Price */}
                <div className={styles.formGroup}>
                  <label className={styles.label}>Price</label>
                  <Input
                    data-testid="price"
                    type="number"
                    placeholder="Enter price"
                    value={demoFormData.price}
                    onChange={(e) => handleInputChange('price', e.target.value)}
                    className={styles.input}
                  />
                </div>

                {/* Quantity */}
                <div className={styles.formGroup}>
                  <label className={styles.label}>Quantity</label>
                  <Input
                    data-testid="quantity"
                    type="number"
                    placeholder="Enter quantity"
                    value={demoFormData.quantity}
                    onChange={(e) => handleInputChange('quantity', e.target.value)}
                    className={styles.input}
                  />
                </div>

                {/* Action Buttons */}
                <div className={styles.buttonGroup}>
                  <Button
                    type="primary"
                    size="large"
                    data-testid="submit-btn"
                    onClick={handleSubmit}
                    block
                  >
                    Submit Form
                  </Button>
                </div>

                {/* Demo Status */}
                <Divider />
                <div className={styles.status}>
                  <Tag color="blue">Demo Status</Tag>
                  <div className={styles.statusContent}>
                    <p><strong>Session ID:</strong> {sessionId.slice(0, 20)}...</p>
                    <p><strong>Form Fields:</strong> 5 inputs ready for AI automation</p>
                    <p><strong>Available Actions:</strong> Click, Input, Reset, Submit</p>
                  </div>
                </div>
              </Space>
            </Card>
          </div>

          {/* MCP Console Panel */}
          {showConsole && (
            <div className={styles.consolePanel}>
              <MCPConsole
                sessionId={sessionId}
                onClose={() => setShowConsole(false)}
              />
            </div>
          )}

          {/* Console Toggle Button (when hidden) */}
          {!showConsole && (
            <Button
              type="primary"
              size="large"
              onClick={() => setShowConsole(true)}
              className={styles.toggleButton}
              style={{
                position: 'fixed',
                right: 20,
                bottom: 20,
                zIndex: 1000,
              }}
            >
              Show Console
            </Button>
          )}
        </div>
      </Content>
    </AppLayout>
  );
};

export default AIAssistantDemo;
