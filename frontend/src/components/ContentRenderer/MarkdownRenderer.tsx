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
          h1: ({ node: _node, ...props }) => <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: '12px 0' }} {...props} />,
          h2: ({ node: _node, ...props }) => <h2 style={{ fontSize: '20px', fontWeight: 'bold', margin: '10px 0' }} {...props} />,
          h3: ({ node: _node, ...props }) => <h3 style={{ fontSize: '18px', fontWeight: 'bold', margin: '8px 0' }} {...props} />,
          ul: ({ node: _node, ...props }) => <ul style={{ marginLeft: '20px', margin: '8px 0' }} {...props} />,
          ol: ({ node: _node, ...props }) => <ol style={{ marginLeft: '20px', margin: '8px 0' }} {...props} />,
          li: ({ node: _node, ...props }) => <li style={{ margin: '4px 0' }} {...props} />,
          code: ({ node: _node, inline, ...props }: any) =>
            inline ? (
              <code style={{ backgroundColor: '#f0f0f0', padding: '2px 6px', borderRadius: '3px', fontFamily: 'monospace' }} {...props} />
            ) : (
              <code style={{ backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '4px', display: 'block', overflow: 'auto', margin: '8px 0', fontFamily: 'monospace' }} {...props} />
            ),
          pre: ({ node: _node, ...props }) => <pre style={{ margin: '0' }} {...props} />,
          table: ({ node: _node, ...props }) => <table style={{ borderCollapse: 'collapse', margin: '8px 0', width: '100%' }} {...props} />,
          th: ({ node: _node, ...props }) => <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left', backgroundColor: '#f5f5f5' }} {...props} />,
          td: ({ node: _node, ...props }) => <td style={{ border: '1px solid #ddd', padding: '8px' }} {...props} />,
          a: ({ node: _node, ...props }) => <a style={{ color: '#1890ff', cursor: 'pointer' }} {...props} />,
          blockquote: ({ node: _node, ...props }) => <blockquote style={{ borderLeft: '4px solid #ddd', paddingLeft: '12px', margin: '8px 0', opacity: 0.8 }} {...props} />,
          p: ({ node: _node, ...props }) => <p style={{ margin: '8px 0', lineHeight: '1.6' }} {...props} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

MarkdownRenderer.displayName = 'MarkdownRenderer';

export default MarkdownRenderer;
