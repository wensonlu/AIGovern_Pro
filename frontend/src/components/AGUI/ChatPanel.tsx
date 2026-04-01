import React, { useState, useEffect, useRef, useMemo, useCallback, memo } from 'react';
import { VariableSizeList as List } from 'react-window';
import { Input, Button, Empty, Badge, Space, Divider, Tag, message, Alert } from 'antd';
import { SendOutlined, CloseOutlined, CopyOutlined, LikeOutlined, DislikeOutlined, MessageOutlined } from '@ant-design/icons';
import { chatWithKnowledge, type ChatResponse } from '../../services/api';
import { useApiCall } from '../../hooks/useApiCall';
import styles from './ChatPanel.module.css';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    document_id?: number | string;
    title: string;
    filename?: string;
    relevance: number;
    relevance_percentage: string;
    text_preview?: string;
  }>;
  confidence?: number;
}

interface SuggestedQuestion {
  id: string;
  text: string;
  icon?: string;
}

// Message row component for virtualization - memoized for performance
const MessageRow = memo<{ index: number; style: React.CSSProperties; messages: Message[]; onCopy: (text: string) => void }>(
  ({ index, style, messages, onCopy }) => {
    const msg = messages[index];

    return (
      <div style={style} className={`${styles.message} ${styles[msg.type]}`}>
        {msg.type === 'assistant' && <div className={styles.avatar}>🤖</div>}

        <div className={styles.messageContent}>
          <p className={styles.text}>{msg.content}</p>
          <p className={styles.timestamp} style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
            {msg.timestamp.toLocaleTimeString()}
          </p>

          {/* 置信度指示器 */}
          {msg.confidence && (
            <div className={styles.confidence}>
              <span>置信度:</span>
              <div className={styles.confidenceBar}>
                <div className={styles.confidenceFill} style={{ width: `${msg.confidence * 100}%` }} />
              </div>
              <span className={styles.confidenceValue}>{(msg.confidence * 100).toFixed(0)}%</span>
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
                    onClick={() => onCopy(source.filename || source.title)}
                  >
                    <span>📄 {source.filename || source.title}</span>
                    <span className={styles.relevance}>{source.relevance_percentage}</span>
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
                onClick={() => onCopy(msg.content)}
                className={styles.actionBtn}
              />
              <Button type="text" size="small" icon={<LikeOutlined />} className={styles.actionBtn} />
              <Button type="text" size="small" icon={<DislikeOutlined />} className={styles.actionBtn} />
            </div>
          )}
        </div>

        {msg.type === 'user' && <div className={styles.avatar}>👤</div>}
      </div>
    );
  },
  // Custom comparison function - only re-render if this specific message changed
  (prevProps, nextProps) => {
    const prevMsg = prevProps.messages[prevProps.index];
    const nextMsg = nextProps.messages[nextProps.index];
    // Skip re-render if same message (by id and content)
    return (
      prevProps.index === nextProps.index &&
      prevMsg?.id === nextMsg?.id &&
      prevMsg?.content === nextMsg?.content &&
      prevMsg?.confidence === nextMsg?.confidence &&
      prevProps.onCopy === nextProps.onCopy
    );
  }
);

MessageRow.displayName = 'MessageRow';

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
  const [lastError, setLastError] = useState<string | null>(null);
  const [sessionId] = useState(() => {
    const stored = localStorage.getItem('chat_session_id');
    if (stored) return stored;
    const newId = `session_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    localStorage.setItem('chat_session_id', newId);
    return newId;
  });
  const listRef = useRef<List>(null);
  // Use message ID as cache key instead of index
  const itemSizeMap = useRef<Map<string, number>>(new Map());

  // Clean up stale itemSizeMap entries when messages change
  useEffect(() => {
    const currentIds = new Set(messages.map(m => m.id));
    const cachedIds = Array.from(itemSizeMap.current.keys());
    for (const cachedId of cachedIds) {
      if (!currentIds.has(cachedId)) {
        itemSizeMap.current.delete(cachedId);
      }
    }
  }, [messages]);

  const { execute: sendChat, loading: chatLoading, retry: retryChat, canRetry } = useApiCall(chatWithKnowledge, {
    errorMessage: '知识问答失败，请重试',
    showMessage: true,
    onSuccess: (response: ChatResponse) => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer || '无法获取回复',
        timestamp: new Date(),
        sources: response.sources || [],
        confidence: response.confidence || 0.8,
      };
      setMessages(prev => [...prev, assistantMessage]);
      setLastError(null);
    },
  });

  const suggestedQuestions: SuggestedQuestion[] = [
    { id: '1', text: '最近7天订单趋势如何？', icon: '📊' },
    { id: '2', text: '哪些产品库存不足？', icon: '📦' },
    { id: '3', text: '如何提升转化率？', icon: '📈' },
  ];

  // Memoize display messages to prevent unnecessary re-renders
  const displayMessages = useMemo(
    () => (chatLoading ? [...messages, { id: 'loading', type: 'assistant' as const, content: 'AI正在思考...', timestamp: new Date() }] : messages),
    [messages, chatLoading]
  );

  // Estimate item height based on content
  const getItemSize = useCallback((index: number) => {
    const msg = displayMessages[index];
    if (!msg) return 120;

    // Use message ID as cache key for stable caching
    const cachedSize = itemSizeMap.current.get(msg.id);
    if (cachedSize) return cachedSize;

    // Base height for message container
    let estimatedHeight = 100;

    // Add height for longer content
    const contentLines = msg.content.split('\n').length;
    estimatedHeight += Math.max(0, (contentLines - 1) * 20);

    // Add height for sources if present
    if (msg.sources && msg.sources.length > 0) {
      estimatedHeight += 30 + (msg.sources.length * 25);
    }

    // Add height for confidence indicator
    if (msg.confidence) {
      estimatedHeight += 30;
    }

    const finalHeight = Math.min(estimatedHeight, 400); // Cap at 400px
    itemSizeMap.current.set(msg.id, finalHeight);
    return finalHeight;
  }, [displayMessages]);

  const handleSendMessage = async (text: string = input) => {
    if (!text.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      await sendChat(text, sessionId, 5);
    } catch (error) {
      console.error('Chat error:', error);
      setLastError('消息发送失败，请点击重试');
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    handleSendMessage(question);
  };

  const handleCopyMessage = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板');
  };

  // Auto-scroll to latest message
  useEffect(() => {
    if (listRef.current && messages.length > 0) {
      // Scroll to the last item
      setTimeout(() => {
        if (listRef.current) {
          listRef.current.scrollToItem(messages.length - 1, 'end');
        }
      }, 0);
    }
  }, [messages]);

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

          {/* Error alert with retry */}
          {lastError && canRetry && (
            <Alert
              type="error"
              message={lastError}
              showIcon
              action={
                <Button size="small" type="primary" onClick={() => {
                  setLastError(null);
                  retryChat();
                }}>
                  重试
                </Button>
              }
              style={{ margin: '8px 0' }}
            />
          )}

          {/* 虚拟化消息列表 */}
          <div className={styles.messageList}>
            {displayMessages.length === 0 ? (
              <Empty description="暂无对话记录" />
            ) : (
              <List
                ref={listRef}
                height={400}
                itemCount={displayMessages.length}
                itemSize={getItemSize}
                width="100%"
              >
                {({ index, style }: { index: number; style: React.CSSProperties }) => (
                  <MessageRow
                    index={index}
                    style={style}
                    messages={displayMessages}
                    onCopy={handleCopyMessage}
                  />
                )}
              </List>
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
