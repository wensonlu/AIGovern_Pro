import React, { useState, useEffect, useRef } from 'react';
import { Input, Button, Spin, Empty, Badge, Space, Divider, Tag, message } from 'antd';
import { SendOutlined, CloseOutlined, CopyOutlined, LikeOutlined, DislikeOutlined, MessageOutlined } from '@ant-design/icons';
import { chatWithKnowledge, type ChatResponse } from '../../services/api';
import { useApiCall } from '../../hooks/useApiCall';
import styles from './ChatPanel.module.css';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{ title: string; url: string; relevance: number }>;
  confidence?: number;
}

interface SuggestedQuestion {
  id: string;
  text: string;
  icon?: string;
}

const ChatPanel: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: '你好！我是AIGovern智能助手，可以帮助你解答企业经营中的各种问题。如：\n• 查询企业知识库\n• 分析业务数据\n• 获取操作指导\n• 经营决策建议',
      timestamp: new Date(),
      sources: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [sessionId] = useState(() => {
    // 生成会话ID，用于维持对话连贯性
    const stored = localStorage.getItem('chat_session_id');
    if (stored) return stored;
    const newId = `session_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    localStorage.setItem('chat_session_id', newId);
    return newId;
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 使用 useApiCall Hook 管理 API 调用
  const { execute: sendChat, loading: chatLoading } = useApiCall(chatWithKnowledge, {
    errorMessage: '知识问答失败，请重试',
    showMessage: true,
    onSuccess: (response: ChatResponse) => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer || '无法获取回复',
        timestamp: new Date(),
        sources: response.sources?.map((src) => ({
          title: src.title,
          url: '#',
          relevance: src.relevance || 0,
        })) || [],
        confidence: response.confidence || 0.8,
      };
      setMessages(prev => [...prev, assistantMessage]);
    },
  });

  const suggestedQuestions: SuggestedQuestion[] = [
    { id: '1', text: '最近7天订单趋势如何？', icon: '📊' },
    { id: '2', text: '哪些产品库存不足？', icon: '📦' },
    { id: '3', text: '如何提升转化率？', icon: '📈' },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (text: string = input) => {
    if (!text.trim()) return;

    // 添加用户消息
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      // 调用真实 API
      await sendChat(text, sessionId, 5);
    } catch (error) {
      // 错误已由 Hook 处理
      console.error('Chat error:', error);
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    handleSendMessage(question);
  };

  const handleCopyMessage = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板');
  };

  return (
    <div className={styles.chatPanelContainer}>
      {/* 悬浮球 */}
      {!isOpen && (
        <div className={styles.floatingBall} onClick={() => setIsOpen(true)}>
          <Badge count={3} color="#00d9ff" className={styles.badge}>
            <MessageOutlined className={styles.ballIcon} />
          </Badge>
        </div>
      )}

      {/* 展开的面板 */}
      {isOpen && (
        <div className={`${styles.chatPanel} ${styles.expanded}`}>
          {/* 面板头部 */}
          <div className={styles.panelHeader}>
            <div className={styles.headerTitle}>
              <Badge color="var(--color-accent-cyan)" />
              <span>智能助手</span>
            </div>
            <Button
              type="text"
              icon={<CloseOutlined />}
              onClick={() => setIsOpen(false)}
              className={styles.collapseBtn}
            />
          </div>

          {/* 消息列表 */}
          <div className={styles.messageList}>
            {messages.length === 0 ? (
              <Empty description="暂无对话记录" />
            ) : (
              <>
                {messages.map((msg) => (
                  <div key={msg.id} className={`${styles.message} ${styles[msg.type]}`}>
                    {msg.type === 'assistant' && (
                      <div className={styles.avatar}>🤖</div>
                    )}

                    <div className={styles.messageContent}>
                      <p className={styles.text}>{msg.content}</p>

                      {/* 置信度指示器 */}
                      {msg.confidence && (
                        <div className={styles.confidence}>
                          <span>置信度:</span>
                          <div className={styles.confidenceBar}>
                            <div
                              className={styles.confidenceFill}
                              style={{ width: `${msg.confidence * 100}%` }}
                            />
                          </div>
                          <span className={styles.confidenceValue}>
                            {(msg.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      )}

                      {/* 信息来源 */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div className={styles.sources}>
                          <div className={styles.sourcesTitle}>📚 信息来源</div>
                          <div className={styles.sourcesList}>
                            {msg.sources.map((source, i) => (
                              <Tag
                                key={i}
                                color="cyan"
                                className={styles.sourceTag}
                                onClick={() => handleCopyMessage(source.title)}
                              >
                                {source.title}
                                <span className={styles.relevance}>
                                  {(source.relevance * 100).toFixed(0)}%
                                </span>
                              </Tag>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 操作按钮 */}
                      {msg.type === 'assistant' && (
                        <div className={styles.messageActions}>
                          <Button
                            type="text"
                            size="small"
                            icon={<CopyOutlined />}
                            onClick={() => handleCopyMessage(msg.content)}
                            className={styles.actionBtn}
                          />
                          <Button
                            type="text"
                            size="small"
                            icon={<LikeOutlined />}
                            className={styles.actionBtn}
                          />
                          <Button
                            type="text"
                            size="small"
                            icon={<DislikeOutlined />}
                            className={styles.actionBtn}
                          />
                        </div>
                      )}
                    </div>

                    {msg.type === 'user' && (
                      <div className={styles.avatar}>👤</div>
                    )}
                  </div>
                ))}

                {chatLoading && (
                  <div className={`${styles.message} ${styles.assistant}`}>
                    <div className={styles.avatar}>🤖</div>
                    <div className={styles.messageContent}>
                      <Spin size="small" tip="AI正在思考..." />
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* 推荐问题（当没有消息或开始时显示） */}
          {messages.length <= 1 && !chatLoading && (
            <div className={styles.suggestedQuestions}>
              <p className={styles.suggestedTitle}>建议提问</p>
              <Space direction="vertical" style={{ width: '100%' }}>
                {suggestedQuestions.map(q => (
                  <Button
                    key={q.id}
                    type="text"
                    block
                    className={styles.suggestedBtn}
                    onClick={() => handleSuggestedQuestion(q.text)}
                  >
                    <span className={styles.suggestedIcon}>{q.icon}</span>
                    <span>{q.text}</span>
                  </Button>
                ))}
              </Space>
            </div>
          )}

          <Divider style={{ margin: '12px 0' }} />

          {/* 输入框 */}
          <div className={styles.inputArea}>
            <Input.TextArea
              placeholder="输入你的问题... (Enter发送 Shift+Enter换行)"
              value={input}
              onChange={e => setInput(e.target.value)}
              onPressEnter={e => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              rows={3}
              className={styles.textarea}
              disabled={chatLoading}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              loading={chatLoading}
              onClick={() => handleSendMessage()}
              className={styles.sendBtn}
              disabled={!input.trim() || chatLoading}
            >
              发送
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatPanel;

