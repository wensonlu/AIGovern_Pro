import React, { useState, useRef, useEffect } from 'react';
import { Card, Input, Button, Space, Spin, Tabs, Empty, AutoComplete, App } from 'antd';
import { SendOutlined, ClearOutlined, CloseOutlined } from '@ant-design/icons';
import OperationLog from './OperationLog';
import ScreenshotViewer from './ScreenshotViewer';
import { streamAiTask } from '../../services/mcp-demo-api';
import styles from './MCPConsole.module.css';

interface ConsoleProps {
  sessionId: string;
  onClose?: () => void;
}

interface Operation {
  type: string;
  sequence?: number;
  tool?: string;
  params?: Record<string, any>;
  message?: string;
  success?: boolean;
  data?: any;
  error?: string;
  content?: string;
  task?: string;
}

const DEMO_PROMPTS = [
  'Click the reset button to clear the form',
  'Fill in product name as "Laptop"',
  'Select "Electronics" from the category dropdown',
  'Fill all fields with sample data and submit the form',
  'Click reset and fill in product name',
];

const MCPConsole: React.FC<ConsoleProps> = ({ sessionId, onClose }) => {
  const { message } = App.useApp();
  const [taskInput, setTaskInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [operations, setOperations] = useState<Operation[]>([]);
  const [currentScreenshot, setCurrentScreenshot] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('log');
  const logEndRef = useRef<HTMLDivElement>(null);
  const [suggestions, setSuggestions] = useState(DEMO_PROMPTS);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [operations]);

  const handleSendTask = async () => {
    if (!taskInput.trim()) {
      message.warning('Please enter a task');
      return;
    }

    setIsLoading(true);
    setOperations([]);
    setCurrentScreenshot(null);

    try {
      for await (const event of streamAiTask(taskInput, sessionId)) {
        setOperations(prev => [...prev, event]);

        // Optional: still support screenshot if returned
        if (event.type === 'screenshot' && event.data) {
          setCurrentScreenshot(event.data);
        }

        if (event.type === 'error') {
          message.error(event.message || 'Task failed');
          break;
        }

        if (event.type === 'done') {
          message.success(`Task completed (${event.tool_calls || 0} tool calls)`);
        }
      }
    } catch (error) {
      message.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setOperations(prev => [...prev, {
        type: 'error',
        message: error instanceof Error ? error.message : 'Unknown error',
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickPrompt = (prompt: string) => {
    setTaskInput(prompt);
  };

  const handleClear = () => {
    setOperations([]);
    setCurrentScreenshot(null);
    setSuggestions(DEMO_PROMPTS);
  };

  const handleTaskInputChange = (value: string) => {
    setTaskInput(value);
    // Filter suggestions
    const filtered = DEMO_PROMPTS.filter(p =>
      p.toLowerCase().includes(value.toLowerCase())
    );
    setSuggestions(value ? filtered : DEMO_PROMPTS);
  };

  return (
    <Card
      className={styles.console}
      title="🤖 AI Assistant Demo"
      extra={
        <Button
          type="text"
          icon={<CloseOutlined />}
          onClick={onClose}
          size="small"
        />
      }
      size="small"
    >
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'log',
            label: `Operations (${operations.length})`,
            children: (
              <div className={styles.logContent}>
                {operations.length === 0 ? (
                  <Empty
                    description="No operations yet"
                    style={{ marginTop: 24 }}
                  />
                ) : (
                  <div className={styles.operationsList}>
                    <OperationLog operations={operations} />
                    <div ref={logEndRef} />
                  </div>
                )}
              </div>
            ),
          },
          {
            key: 'screenshot',
            label: 'Screenshot',
            children: currentScreenshot ? (
              <ScreenshotViewer image={currentScreenshot} />
            ) : (
              <Empty description="No screenshot yet" style={{ marginTop: 24 }} />
            ),
          },
        ]}
      />

      <div className={styles.inputSection}>
        <AutoComplete
          value={taskInput}
          onChange={handleTaskInputChange}
          options={suggestions.map(s => ({ label: s, value: s }))}
          placeholder="Describe your task..."
          className={styles.input}
          onSelect={(value) => setTaskInput(value)}
          disabled={isLoading}
        />

        <Space className={styles.buttonGroup}>
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSendTask}
            loading={isLoading}
            disabled={!taskInput.trim() || isLoading}
          >
            Send
          </Button>
          <Button
            icon={<ClearOutlined />}
            onClick={handleClear}
            disabled={isLoading}
          >
            Clear
          </Button>
        </Space>
      </div>

      {isLoading && (
        <div className={styles.loading}>
          <Spin size="small" />
          <span>Processing...</span>
        </div>
      )}

      <div className={styles.tips}>
        <p className={styles.tipTitle}>💡 Quick Examples:</p>
        <div className={styles.quickPrompts}>
          {DEMO_PROMPTS.slice(0, 3).map((prompt, idx) => (
            <Button
              key={idx}
              type="text"
              size="small"
              onClick={() => handleQuickPrompt(prompt)}
              className={styles.quickButton}
              disabled={isLoading}
            >
              {prompt}
            </Button>
          ))}
        </div>
      </div>
    </Card>
  );
};

export default MCPConsole;
