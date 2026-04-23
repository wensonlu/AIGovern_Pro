# 多格式内容渲染系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a pluggable multi-format content renderer system supporting Markdown, HTML, JSON, and plain text, with a registry pattern for future extensibility.

**Architecture:** ContentRenderer is a registry-based dispatcher. Each format has a dedicated renderer component. Message interface extends with `content_type` field. ChatPanel's MessageRow delegates to `getContentRenderer()` to select the appropriate component. Stream events now include a `format` event before delta content.

**Tech Stack:** React 18, TypeScript, react-markdown, remark-gfm

---

## File Structure

```
frontend/src/components/
├── ContentRenderer/                          # NEW DIRECTORY
│   ├── index.ts                              # Public export
│   ├── types.ts                              # Type definitions
│   ├── registry.ts                           # Factory function
│   ├── TextRenderer.tsx                      # Plain text renderer
│   ├── MarkdownRenderer.tsx                  # Markdown renderer
│   ├── HtmlRenderer.tsx                      # HTML renderer
│   ├── JsonRenderer.tsx                      # JSON renderer
│   └── __tests__/
│       └── registry.test.ts                  # Registry unit tests
├── AGUI/
│   └── ChatPanel.tsx                         # MODIFY: integrate ContentRenderer
└── (existing files)

frontend/src/services/
└── api.ts                                    # MODIFY: handle format event in stream
```

---

## Task 1: Extend Message Type

**Files:**
- Modify: `frontend/src/components/AGUI/ChatPanel.tsx:8-15`

- [ ] **Step 1: Update Message interface**

Replace the current Message interface with:

```typescript
interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  content_type?: 'text' | 'markdown' | 'html' | 'json';  // NEW: default 'text'
  timestamp: Date;
  sources?: SourceReference[];
  confidence?: number;
}
```

- [ ] **Step 2: Update initial message (line 109)**

Change the initial assistant greeting to include `content_type`:

```typescript
{
  id: '1',
  type: 'assistant',
  content: '你好！我是AIGovern智能助手，可以帮助你解答企业经营中的各种问题。如：\n• 查询企业知识库\n• 分析业务数据\n• 获取操作指导\n• 经营决策建议',
  content_type: 'text',
  timestamp: new Date(),
  sources: [],
}
```

- [ ] **Step 3: Commit**

```bash
cd frontend
git add src/components/AGUI/ChatPanel.tsx
git commit -m "refactor: add content_type field to Message interface"
```

---

## Task 2: Create ContentRenderer Type Definitions

**Files:**
- Create: `frontend/src/components/ContentRenderer/types.ts`

- [ ] **Step 1: Create types file**

```typescript
import { ReactNode } from 'react';

export type ContentType = 'text' | 'markdown' | 'html' | 'json';

export interface ContentRendererProps {
  content: string;
  className?: string;
}

export interface ContentRendererComponent {
  (props: ContentRendererProps): ReactNode;
  displayName?: string;
}
```

- [ ] **Step 2: Commit**

```bash
cd frontend
git add src/components/ContentRenderer/types.ts
git commit -m "feat: add ContentRenderer type definitions"
```


---

## Task 3: Create TextRenderer Component

**Files:**
- Create: `frontend/src/components/ContentRenderer/TextRenderer.tsx`

- [ ] **Step 1: Create TextRenderer**

```typescript
import React from 'react';
import { ContentRendererProps } from './types';

const TextRenderer: React.FC<ContentRendererProps> = ({ content, className }) => {
  // Split by newlines, preserve line breaks in rendering
  const lines = content.split('\n');

  return (
    <div className={className}>
      {lines.map((line, index) => (
        <React.Fragment key={index}>
          <span>{line}</span>
          {index < lines.length - 1 && <br />}
        </React.Fragment>
      ))}
    </div>
  );
};

TextRenderer.displayName = 'TextRenderer';

export default TextRenderer;
```

- [ ] **Step 2: Commit**

```bash
cd frontend
git add src/components/ContentRenderer/TextRenderer.tsx
git commit -m "feat: implement TextRenderer component"
```

---

## Task 4: Create Registry Factory

**Files:**
- Create: `frontend/src/components/ContentRenderer/registry.ts`
- Create: `frontend/src/components/ContentRenderer/index.ts`

- [ ] **Step 1: Create registry.ts**

```typescript
import { FC } from 'react';
import TextRenderer from './TextRenderer';
import MarkdownRenderer from './MarkdownRenderer';
import HtmlRenderer from './HtmlRenderer';
import JsonRenderer from './JsonRenderer';
import { ContentRendererProps, ContentType } from './types';

type RendererMap = {
  [key in ContentType]: FC<ContentRendererProps>;
};

const renderers: RendererMap = {
  text: TextRenderer,
  markdown: MarkdownRenderer,
  html: HtmlRenderer,
  json: JsonRenderer,
};

export const getContentRenderer = (contentType?: string | null): FC<ContentRendererProps> => {
  const type = contentType as ContentType | undefined;
  if (type && type in renderers) {
    return renderers[type];
  }
  return renderers.text; // Fallback to text
};

export const registerRenderer = (type: ContentType, component: FC<ContentRendererProps>) => {
  renderers[type] = component;
};

export const getRegisteredTypes = (): ContentType[] => {
  return Object.keys(renderers) as ContentType[];
};
```

- [ ] **Step 2: Create index.ts**

```typescript
export { getContentRenderer, registerRenderer, getRegisteredTypes } from './registry';
export type { ContentType, ContentRendererProps } from './types';
export { default as TextRenderer } from './TextRenderer';
export { default as MarkdownRenderer } from './MarkdownRenderer';
export { default as HtmlRenderer } from './HtmlRenderer';
export { default as JsonRenderer } from './JsonRenderer';
```

- [ ] **Step 3: Create directory**

```bash
cd frontend
mkdir -p src/components/ContentRenderer/__tests__
```

- [ ] **Step 4: Commit**

```bash
cd frontend
git add src/components/ContentRenderer/registry.ts src/components/ContentRenderer/index.ts
git commit -m "feat: implement ContentRenderer registry and factory pattern"
```

---

## Task 5: Install Dependencies

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install react-markdown and remark-gfm**

```bash
cd frontend
pnpm add react-markdown remark-gfm
```

- [ ] **Step 2: Verify installation**

```bash
cd frontend
pnpm list react-markdown remark-gfm
```

Expected: Both packages listed with versions ^9.0+ and ^4.0+ respectively.

- [ ] **Step 3: Commit**

```bash
cd frontend
git add pnpm-lock.yaml package.json
git commit -m "deps: add react-markdown and remark-gfm for markdown support"
```

---

## Task 6: Create MarkdownRenderer Component

**Files:**
- Create: `frontend/src/components/ContentRenderer/MarkdownRenderer.tsx`

- [ ] **Step 1: Create MarkdownRenderer**

```typescript
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ContentRendererProps } from './types';

const MarkdownRenderer: React.FC<ContentRendererProps> = ({ content, className }) => {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ node, ...props }) => <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: '12px 0' }} {...props} />,
          h2: ({ node, ...props }) => <h2 style={{ fontSize: '20px', fontWeight: 'bold', margin: '10px 0' }} {...props} />,
          h3: ({ node, ...props }) => <h3 style={{ fontSize: '18px', fontWeight: 'bold', margin: '8px 0' }} {...props} />,
          ul: ({ node, ...props }) => <ul style={{ marginLeft: '20px', margin: '8px 0' }} {...props} />,
          ol: ({ node, ...props }) => <ol style={{ marginLeft: '20px', margin: '8px 0' }} {...props} />,
          li: ({ node, ...props }) => <li style={{ margin: '4px 0' }} {...props} />,
          code: ({ node, inline, ...props }) => 
            inline ? (
              <code style={{ backgroundColor: '#f0f0f0', padding: '2px 6px', borderRadius: '3px', fontFamily: 'monospace' }} {...props} />
            ) : (
              <code style={{ backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '4px', display: 'block', overflow: 'auto', margin: '8px 0', fontFamily: 'monospace' }} {...props} />
            ),
          pre: ({ node, ...props }) => <pre style={{ margin: '0' }} {...props} />,
          table: ({ node, ...props }) => <table style={{ borderCollapse: 'collapse', margin: '8px 0', width: '100%' }} {...props} />,
          th: ({ node, ...props }) => <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left', backgroundColor: '#f5f5f5' }} {...props} />,
          td: ({ node, ...props }) => <td style={{ border: '1px solid #ddd', padding: '8px' }} {...props} />,
          a: ({ node, ...props }) => <a style={{ color: '#1890ff', cursor: 'pointer' }} {...props} />,
          blockquote: ({ node, ...props }) => <blockquote style={{ borderLeft: '4px solid #ddd', paddingLeft: '12px', margin: '8px 0', opacity: 0.8 }} {...props} />,
          p: ({ node, ...props }) => <p style={{ margin: '8px 0', lineHeight: '1.6' }} {...props} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

MarkdownRenderer.displayName = 'MarkdownRenderer';

export default MarkdownRenderer;
```

- [ ] **Step 2: Commit**

```bash
cd frontend
git add src/components/ContentRenderer/MarkdownRenderer.tsx
git commit -m "feat: implement MarkdownRenderer with GFM support"
```


---

## Task 7: Create HtmlRenderer Component

**Files:**
- Create: `frontend/src/components/ContentRenderer/HtmlRenderer.tsx`

- [ ] **Step 1: Create HtmlRenderer**

⚠️ **Security Note:** This uses `dangerouslySetInnerHTML`. Per the design spec, we trust the backend has sanitized content. Do NOT use this for untrusted user content.

```typescript
import React from 'react';
import { ContentRendererProps } from './types';

const HtmlRenderer: React.FC<ContentRendererProps> = ({ content, className }) => {
  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: content }}
      style={{ wordBreak: 'break-word', overflowWrap: 'break-word' }}
    />
  );
};

HtmlRenderer.displayName = 'HtmlRenderer';

export default HtmlRenderer;
```

- [ ] **Step 2: Commit**

```bash
cd frontend
git add src/components/ContentRenderer/HtmlRenderer.tsx
git commit -m "feat: implement HtmlRenderer (backend-sanitized content only)"
```

---

## Task 8: Create JsonRenderer Component

**Files:**
- Create: `frontend/src/components/ContentRenderer/JsonRenderer.tsx`

- [ ] **Step 1: Create JsonRenderer**

```typescript
import React, { useState } from 'react';
import { ContentRendererProps } from './types';

const JsonRenderer: React.FC<ContentRendererProps> = ({ content, className }) => {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  let parsedData: unknown;
  try {
    parsedData = JSON.parse(content);
  } catch (e) {
    return (
      <div className={className} style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '12px' }}>
        <span style={{ color: '#d32f2f' }}>Invalid JSON:</span>
        {'\n'}
        {content}
      </div>
    );
  }

  const toggleKey = (key: string) => {
    const newExpanded = new Set(expandedKeys);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedKeys(newExpanded);
  };

  const renderValue = (value: unknown, path: string = 'root', depth: number = 0): React.ReactNode => {
    const isExpanded = expandedKeys.has(path);
    const indent = depth * 16;

    if (value === null) {
      return <span style={{ color: '#d32f2f' }}>null</span>;
    }

    if (typeof value === 'boolean') {
      return <span style={{ color: '#1976d2' }}>{String(value)}</span>;
    }

    if (typeof value === 'number') {
      return <span style={{ color: '#388e3c' }}>{value}</span>;
    }

    if (typeof value === 'string') {
      return <span style={{ color: '#d32f2f' }}>"{value}"</span>;
    }

    if (Array.isArray(value)) {
      return (
        <div>
          <div onClick={() => toggleKey(path)} style={{ cursor: 'pointer', paddingLeft: `${indent}px`, userSelect: 'none' }}>
            <span style={{ marginRight: '4px' }}>{isExpanded ? '▼' : '▶'}</span>
            <span>[ {value.length} items ]</span>
          </div>
          {isExpanded && value.map((item, idx) => (
            <div key={idx} style={{ paddingLeft: `${indent + 16}px` }}>
              <span style={{ color: '#666' }}>[{idx}]:</span> {renderValue(item, `${path}[${idx}]`, depth + 1)}
            </div>
          ))}
        </div>
      );
    }

    if (typeof value === 'object') {
      const entries = Object.entries(value as Record<string, unknown>);
      return (
        <div>
          <div onClick={() => toggleKey(path)} style={{ cursor: 'pointer', paddingLeft: `${indent}px`, userSelect: 'none' }}>
            <span style={{ marginRight: '4px' }}>{isExpanded ? '▼' : '▶'}</span>
            <span>{{ {entries.length} properties }}</span>
          </div>
          {isExpanded && entries.map(([key, val]) => (
            <div key={key} style={{ paddingLeft: `${indent + 16}px` }}>
              <span style={{ color: '#1976d2' }}>"{key}":</span> {renderValue(val, `${path}.${key}`, depth + 1)}
            </div>
          ))}
        </div>
      );
    }

    return <span>{String(value)}</span>;
  };

  return (
    <div className={className} style={{ fontFamily: 'monospace', fontSize: '12px', lineHeight: '1.6', color: '#333' }}>
      {renderValue(parsedData)}
    </div>
  );
};

JsonRenderer.displayName = 'JsonRenderer';

export default JsonRenderer;
```

- [ ] **Step 2: Commit**

```bash
cd frontend
git add src/components/ContentRenderer/JsonRenderer.tsx
git commit -m "feat: implement JsonRenderer with collapsible tree view"
```

---

## Task 9: Unit Test Registry

**Files:**
- Create: `frontend/src/components/ContentRenderer/__tests__/registry.test.ts`

- [ ] **Step 1: Create registry tests**

```typescript
import { getContentRenderer, registerRenderer, getRegisteredTypes } from '../registry';
import TextRenderer from '../TextRenderer';
import MarkdownRenderer from '../MarkdownRenderer';
import HtmlRenderer from '../HtmlRenderer';
import JsonRenderer from '../JsonRenderer';

describe('ContentRenderer Registry', () => {
  describe('getContentRenderer', () => {
    it('should return TextRenderer for type "text"', () => {
      const renderer = getContentRenderer('text');
      expect(renderer).toBe(TextRenderer);
    });

    it('should return MarkdownRenderer for type "markdown"', () => {
      const renderer = getContentRenderer('markdown');
      expect(renderer).toBe(MarkdownRenderer);
    });

    it('should return HtmlRenderer for type "html"', () => {
      const renderer = getContentRenderer('html');
      expect(renderer).toBe(HtmlRenderer);
    });

    it('should return JsonRenderer for type "json"', () => {
      const renderer = getContentRenderer('json');
      expect(renderer).toBe(JsonRenderer);
    });

    it('should fallback to TextRenderer for unknown type', () => {
      const renderer = getContentRenderer('unknown');
      expect(renderer).toBe(TextRenderer);
    });

    it('should fallback to TextRenderer for undefined type', () => {
      const renderer = getContentRenderer(undefined);
      expect(renderer).toBe(TextRenderer);
    });

    it('should fallback to TextRenderer for null type', () => {
      const renderer = getContentRenderer(null);
      expect(renderer).toBe(TextRenderer);
    });
  });

  describe('getRegisteredTypes', () => {
    it('should return all registered types', () => {
      const types = getRegisteredTypes();
      expect(types).toContain('text');
      expect(types).toContain('markdown');
      expect(types).toContain('html');
      expect(types).toContain('json');
      expect(types.length).toBe(4);
    });
  });

  describe('registerRenderer', () => {
    it('should allow registering custom renderers', () => {
      const customRenderer = () => <div>Custom</div>;
      registerRenderer('text', customRenderer as any);
      const renderer = getContentRenderer('text');
      expect(renderer).toBe(customRenderer);
    });
  });
});
```

- [ ] **Step 2: Run tests**

```bash
cd frontend
pnpm test -- src/components/ContentRenderer/__tests__/registry.test.ts --watch=false
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
cd frontend
git add src/components/ContentRenderer/__tests__/registry.test.ts
git commit -m "test: add registry unit tests"
```

---

## Task 10: Integrate ContentRenderer into ChatPanel

**Files:**
- Modify: `frontend/src/components/AGUI/ChatPanel.tsx`

- [ ] **Step 1: Add import at top of file**

After the existing imports (line 5), add:

```typescript
import { getContentRenderer } from '../ContentRenderer';
```

- [ ] **Step 2: Update MessageRow component**

Replace the MessageRow constant with:

```typescript
const MessageRow = memo<{ message: Message; onCopy: (text: string) => void }>(
  ({ message: msg, onCopy }) => {
    const ContentComponent = getContentRenderer(msg.content_type);

    return (
      <div className={`${styles.message} ${styles[msg.type]}`}>
        {msg.type === 'assistant' && <div className={styles.avatar}>🤖</div>}

        <div className={styles.messageContent}>
          <ContentComponent content={msg.content} className={styles.text} />
          <p className={styles.timestamp} style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
            {msg.timestamp.toLocaleTimeString()}
          </p>

          {msg.confidence && (
            <div className={styles.confidence}>
              <span>置信度:</span>
              <div className={styles.confidenceBar}>
                <div className={styles.confidenceFill} style={{ width: `${msg.confidence * 100}%` }} />
              </div>
              <span className={styles.confidenceValue}>{(msg.confidence * 100).toFixed(0)}%</span>
            </div>
          )}

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
```

- [ ] **Step 3: Update assistantMessage initialization**

In handleSendMessage function, ensure assistantMessage includes content_type:

```typescript
const assistantMessage: Message = {
  id: assistantMessageId,
  type: 'assistant',
  content: '正在检索知识库...',
  content_type: 'text',
  timestamp: new Date(),
  sources: [],
};
```

- [ ] **Step 4: Verify TypeScript checks**

```bash
cd frontend
pnpm type-check
```

Expected: No errors.

- [ ] **Step 5: Commit**

```bash
cd frontend
git add src/components/AGUI/ChatPanel.tsx
git commit -m "refactor: integrate ContentRenderer into ChatPanel MessageRow"
```

---

## Task 11: Final Verification

**Files:**
- All modified/created files

- [ ] **Step 1: Run linter**

```bash
cd frontend
pnpm lint
```

Expected: No errors.

- [ ] **Step 2: Run type check**

```bash
cd frontend
pnpm type-check
```

Expected: No errors.

- [ ] **Step 3: Run tests**

```bash
cd frontend
pnpm test -- --watch=false
```

Expected: All tests pass.

- [ ] **Step 4: Build and verify**

```bash
cd frontend
pnpm build
```

Expected: Build succeeds.

---

## Success Criteria

- ✅ All 4 formats (text, markdown, html, json) render correctly
- ✅ ChatPanel preserves all existing functionality (sources, confidence, actions)
- ✅ Registry pattern allows future format extension
- ✅ All tests pass
- ✅ No TypeScript/ESLint errors
- ✅ Build succeeds

---

## Rollback Plan

```bash
git revert --no-edit <commit-hash>  # Revert in reverse chronological order
pnpm install
pnpm dev
```

