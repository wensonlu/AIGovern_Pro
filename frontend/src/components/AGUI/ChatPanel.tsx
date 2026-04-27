/* eslint-disable react/prop-types */
import React, { useState, useEffect, useRef, useCallback, memo } from 'react';
import { Input, Button, Empty, Badge, Space, Divider, Tag, message, Alert } from 'antd';
import { SendOutlined, CloseOutlined, CopyOutlined, LikeOutlined, DislikeOutlined, MessageOutlined } from '@ant-design/icons';
import { streamChatWithKnowledge, type SourceReference } from '../../services/api';
import { getContentRenderer } from '../ContentRenderer';
import styles from './ChatPanel.module.css';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  content_type?: 'text' | 'markdown' | 'html' | 'json' | 'structured';
  timestamp: Date;
  sources?: SourceReference[];
  confidence?: number;
}

interface SuggestedQuestion {
  id: string;
  text: string;
  icon?: string;
}

// 自动检测内容格式
function detectContentFormat(content: string): 'text' | 'markdown' | 'html' | 'json' | 'structured' {
  // 优先检测 structured 和 section（最特殊）
  if (content.trim().startsWith('{') || content.trim().startsWith('[')) {
    try {
      const parsed = JSON.parse(content);

      // 检查是否为完整的结构化格式（有 sections 数组字段）
      if (parsed && typeof parsed === 'object' && 'sections' in parsed && Array.isArray(parsed.sections)) {
        return 'structured';
      }

      // 检查是否为单个 section 对象
      if (parsed && typeof parsed === 'object' && 'type' in parsed) {
        const type = parsed.type;
        if (['text', 'list_ordered', 'list_unordered', 'code_block', 'table'].includes(type)) {
          return 'structured';  // 单个 section 也用 StructuredRenderer 处理
        }
      }

      // 否则是普通 JSON
      return 'json';
    } catch {}
  }

  // 检测 HTML
  if (content.includes('<') && content.includes('>')) {
    return 'html';
  }

  // 检测 Markdown
  if (
    content.includes('#') || // 标题
    content.includes('**') || // 加粗
    content.includes('- ') || // 列表
    content.includes('```') // 代码块
  ) {
    return 'markdown';
  }

  return 'text';
}

// Memoized so typing in the input does not re-render stable message rows.
const MessageRow = memo<{ message: Message; onCopy: (text: string) => void }>(
  ({ message: msg, onCopy }) => {
    // 如果没有 content_type，自动检测
    const detectedType = msg.content_type || detectContentFormat(msg.content);
    const ContentComponent = getContentRenderer(detectedType);

    return (
      <div className={`${styles.message} ${styles[msg.type]}`}>
        {msg.type === 'assistant' && <div className={styles.avatar}>🤖</div>}

        <div className={styles.messageContent}>
          <ContentComponent content={msg.content} className={styles.text} />
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
    const prevMsg = prevProps.message;
    const nextMsg = nextProps.message;

    return (
      prevMsg?.id === nextMsg?.id &&
      prevMsg?.content === nextMsg?.content &&
      prevMsg?.content_type === nextMsg?.content_type &&
      prevMsg?.confidence === nextMsg?.confidence &&
      prevMsg?.sources === nextMsg?.sources &&
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
      content_type: 'text',
      timestamp: new Date(),
      sources: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);
  const [sessionId] = useState(() => {
    const stored = localStorage.getItem('chat_session_id');
    if (stored) return stored;
    const newId = `session_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    localStorage.setItem('chat_session_id', newId);
    return newId;
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastFailedTextRef = useRef<string | null>(null);
  const pendingDeltaRef = useRef('');
  const pendingSectionsRef = useRef<any[]>([]);
  const pendingSourcesRef = useRef<SourceReference[]>([]);
  const pendingConfidenceRef = useRef<number | undefined>(undefined);
  const pendingAssistantIdRef = useRef<string | null>(null);
  const deltaFrameRef = useRef<number | null>(null);
  const isStructuredStreamRef = useRef(false);

  const suggestedQuestions: SuggestedQuestion[] = [
    { id: '1', text: '最近7天订单趋势如何？', icon: '📊' },
    { id: '2', text: '哪些产品库存不足？', icon: '📦' },
    { id: '3', text: '如何提升转化率？', icon: '📈' },
  ];

  const updateAssistantMessage = useCallback((id: string, updater: (message: Message) => Message) => {
    setMessages(prev => prev.map(msg => (msg.id === id ? updater(msg) : msg)));
  }, []);

  const flushPendingDelta = useCallback(() => {
    const content = pendingDeltaRef.current;
    const sections = pendingSectionsRef.current;
    const assistantId = pendingAssistantIdRef.current;
    const isStructuredStream = isStructuredStreamRef.current;

    pendingDeltaRef.current = '';
    pendingSectionsRef.current = [];
    deltaFrameRef.current = null;

    if (!assistantId) return;

    // 如果收到了结构化的 sections，构建完整的 StructuredContent
    if (sections.length > 0 && isStructuredStream) {
      const structuredContent = {
        sections: sections,
      };
      const contentJson = JSON.stringify(structuredContent);
      updateAssistantMessage(assistantId, msg => ({
        ...msg,
        content: contentJson,
        content_type: 'structured',
      }));
      return;
    }

    // 否则处理普通文本流
    if (!content) return;

    updateAssistantMessage(assistantId, msg => {
      const newContent = msg.content === '正在检索知识库...' ? content : `${msg.content}${content}`;
      const newContentType = msg.content_type || detectContentFormat(newContent);
      return {
        ...msg,
        content: newContent,
        content_type: newContentType,
      };
    });
  }, [updateAssistantMessage]);

  const appendAssistantDelta = useCallback((assistantId: string, content: string) => {
    pendingAssistantIdRef.current = assistantId;
    pendingDeltaRef.current += content;

    if (deltaFrameRef.current !== null) return;

    deltaFrameRef.current = window.requestAnimationFrame(flushPendingDelta);
  }, [flushPendingDelta]);

  useEffect(() => {
    return () => {
      if (deltaFrameRef.current !== null) {
        window.cancelAnimationFrame(deltaFrameRef.current);
      }
    };
  }, []);

  const handleSendMessage = async (text: string = input) => {
    const question = text.trim();
    if (!question || isStreaming) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: question,
      timestamp: new Date(),
    };
    const assistantMessageId = `${Date.now()}_assistant`;
    const assistantMessage: Message = {
      id: assistantMessageId,
      type: 'assistant',
      content: '正在检索知识库...',
      timestamp: new Date(),
      sources: [],
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setInput('');
    setIsStreaming(true);
    setLastError(null);
    lastFailedTextRef.current = null;
    pendingDeltaRef.current = '';
    pendingSectionsRef.current = [];
    pendingSourcesRef.current = [];
    pendingConfidenceRef.current = undefined;
    pendingAssistantIdRef.current = assistantMessageId;
    isStructuredStreamRef.current = false;
    if (deltaFrameRef.current !== null) {
      window.cancelAnimationFrame(deltaFrameRef.current);
      deltaFrameRef.current = null;
    }

    try {
      const response = await streamChatWithKnowledge(question, sessionId, 5, {
        onSources: event => {
          pendingSourcesRef.current = event.sources || [];
          pendingConfidenceRef.current = event.confidence;
          isStructuredStreamRef.current = true;  // 标记为结构化流
        },
        onSection: section => {
          // 收集 section 对象
          if (section) {
            pendingSectionsRef.current.push(section);
          }
        },
        onDelta: content => {
          appendAssistantDelta(assistantMessageId, content);
        },
        onDone: event => {
          flushPendingDelta();
          updateAssistantMessage(assistantMessageId, msg => ({
            ...msg,
            sources: pendingSourcesRef.current,
            confidence: event.confidence ?? pendingConfidenceRef.current ?? msg.confidence,
          }));
          pendingSourcesRef.current = [];
          pendingConfidenceRef.current = undefined;
        },
      });

      flushPendingDelta();
      updateAssistantMessage(assistantMessageId, msg => ({
        ...msg,
        sources: response.sources?.length ? response.sources : msg.sources,
        confidence: response.confidence ?? msg.confidence,
      }));
    } catch (error) {
      console.error('Chat error:', error);
      flushPendingDelta();
      lastFailedTextRef.current = question;
      setLastError('消息发送失败，请点击重试');
      updateAssistantMessage(assistantMessageId, msg => ({
        ...msg,
        content: msg.content === '正在检索知识库...' ? '消息发送失败，请稍后重试。' : msg.content,
        confidence: 0,
      }));
      message.error('知识问答失败，请重试');
    } finally {
      setIsStreaming(false);
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    handleSendMessage(question);
  };

  const handleCopyMessage = useCallback((text: string) => {
    navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板');
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ block: 'end' });
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
          {lastError && lastFailedTextRef.current && (
            <Alert
              type="error"
              message={lastError}
              showIcon
              action={
                <Button size="small" type="primary" onClick={() => {
                  setLastError(null);
                  handleSendMessage(lastFailedTextRef.current || '');
                }}>
                  重试
                </Button>
              }
              style={{ margin: '8px 0' }}
            />
          )}

          {/* 消息列表 */}
          <div className={styles.messageList}>
            {messages.length === 0 ? (
              <Empty description="暂无对话记录" />
            ) : (
              <>
                {messages.map(msg => (
                  <MessageRow
                    key={msg.id}
                    message={msg}
                    onCopy={handleCopyMessage}
                  />
                ))}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* 推荐问题（当没有消息或开始时显示） */}
          {messages.length <= 1 && !isStreaming && (
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
              disabled={isStreaming}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              loading={isStreaming}
              onClick={() => handleSendMessage()}
              className={styles.sendBtn}
              disabled={!input.trim() || isStreaming}
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
