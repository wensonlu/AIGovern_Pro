import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ContentRendererProps } from './types';

const MarkdownRenderer: React.FC<ContentRendererProps> = ({ content, className }) => {
  return (
    <div className={className} style={{ wordBreak: 'break-word' }}>
      <style>{`
        .markdown-content ol {
          list-style-type: decimal;
          padding-left: 2em;
        }
        .markdown-content ol ol {
          list-style-type: lower-alpha;
          margin-top: 4px;
          margin-bottom: 4px;
        }
        .markdown-content ol ol ol {
          list-style-type: lower-roman;
        }
        .markdown-content ul {
          list-style-type: disc;
          padding-left: 2em;
        }
        .markdown-content ul ul {
          list-style-type: circle;
          margin-top: 4px;
          margin-bottom: 4px;
        }
        .markdown-content ul ul ul {
          list-style-type: square;
        }
        .markdown-content li {
          margin: 6px 0;
          line-height: 1.6;
        }
      `}</style>
      <div className="markdown-content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ node: _node, ...props }) => <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: '16px 0 8px 0' }} {...props} />,
            h2: ({ node: _node, ...props }) => <h2 style={{ fontSize: '20px', fontWeight: 'bold', margin: '14px 0 8px 0' }} {...props} />,
            h3: ({ node: _node, ...props }) => <h3 style={{ fontSize: '18px', fontWeight: 'bold', margin: '12px 0 6px 0' }} {...props} />,
            h4: ({ node: _node, ...props }) => <h4 style={{ fontSize: '16px', fontWeight: 'bold', margin: '10px 0 4px 0' }} {...props} />,
            h5: ({ node: _node, ...props }) => <h5 style={{ fontSize: '14px', fontWeight: 'bold', margin: '8px 0 4px 0' }} {...props} />,
            h6: ({ node: _node, ...props }) => <h6 style={{ fontSize: '12px', fontWeight: 'bold', margin: '8px 0 4px 0' }} {...props} />,
            // 列表
            ul: ({ node: _node, ...props }) => <ul style={{ margin: '8px 0' }} {...props} />,
            ol: ({ node: _node, ...props }) => <ol style={{ margin: '8px 0' }} {...props} />,
            li: ({ node: _node, ...props }) => <li {...props} />,
            // 代码
            code: ({ node: _node, inline, ...props }: any) =>
              inline ? (
                <code style={{
                  backgroundColor: '#f0f0f0',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  fontFamily: 'monospace',
                  fontSize: '0.9em',
                  color: '#d63384'
                }} {...props} />
              ) : (
                <code style={{
                  backgroundColor: '#f5f5f5',
                  padding: '10px',
                  borderRadius: '4px',
                  display: 'block',
                  overflow: 'auto',
                  margin: '8px 0',
                  fontFamily: 'monospace',
                  fontSize: '13px',
                  lineHeight: '1.4'
                }} {...props} />
              ),
            pre: ({ node: _node, ...props }) => <pre style={{ margin: '0', backgroundColor: '#f5f5f5', padding: '0', borderRadius: '4px' }} {...props} />,
            // 表格
            table: ({ node: _node, ...props }) => <table style={{ borderCollapse: 'collapse', margin: '8px 0', width: '100%' }} {...props} />,
            thead: ({ node: _node, ...props }) => <thead style={{ backgroundColor: '#f5f5f5' }} {...props} />,
            tbody: ({ node: _node, ...props }) => <tbody {...props} />,
            tr: ({ node: _node, ...props }) => <tr {...props} />,
            th: ({ node: _node, ...props }) => <th style={{ border: '1px solid #ddd', padding: '10px', textAlign: 'left', fontWeight: 'bold' }} {...props} />,
            td: ({ node: _node, ...props }) => <td style={{ border: '1px solid #ddd', padding: '10px' }} {...props} />,
            // 链接
            a: ({ node: _node, ...props }) => <a style={{ color: '#1890ff', textDecoration: 'underline', cursor: 'pointer' }} {...props} />,
            // 引用
            blockquote: ({ node: _node, ...props }) => <blockquote style={{
              borderLeft: '4px solid #ddd',
              paddingLeft: '12px',
              margin: '8px 0',
              color: '#666',
              fontStyle: 'italic'
            }} {...props} />,
            // 段落
            p: ({ node: _node, ...props }) => <p style={{ margin: '8px 0', lineHeight: '1.6' }} {...props} />,
            // 分割线
            hr: ({ node: _node, ...props }) => <hr style={{ margin: '16px 0', border: 'none', borderTop: '1px solid #ddd' }} {...props} />,
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
};

MarkdownRenderer.displayName = 'MarkdownRenderer';

export default MarkdownRenderer;
