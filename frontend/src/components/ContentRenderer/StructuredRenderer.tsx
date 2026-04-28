import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ContentRendererProps } from './types';

interface SourceReference {
  document_id: number;
  title: string;
  filename?: string;
  relevance: number;
  relevance_percentage: string;
  text_preview: string;
}

interface ListItem {
  title: string;
  details_markdown?: string;
  subitems?: ListItem[];
}

type Section =
  | { type: 'text'; markdown: string }
  | { type: 'list_ordered'; items: ListItem[] }
  | { type: 'list_unordered'; items: ListItem[] }
  | { type: 'code_block'; language: string; code: string }
  | { type: 'table'; headers: string[]; rows: string[][] };

interface StructuredContent {
  sections: Section[];
  sources?: SourceReference[];
  confidence?: number;
}

const renderListItem = (item: ListItem, depth: number = 0) => {
  const paddingLeft = `${depth * 1.5}rem`;
  return (
    <div key={item.title} style={{ paddingLeft, marginBottom: '4px' }}>
      <strong style={{ display: 'block', marginBottom: '4px' }}>{item.title}</strong>
      {item.details_markdown && (
        <div style={{ marginTop: '4px', marginBottom: '4px', lineHeight: '1.6' }}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ node, ...props }) => <p style={{ margin: '2px 0' }} {...props} />,
              ul: ({ node, ...props }) => <ul style={{ marginLeft: '1em', marginTop: '2px', marginBottom: '2px' }} {...props} />,
              ol: ({ node, ...props }) => <ol style={{ marginLeft: '1em', marginTop: '2px', marginBottom: '2px' }} {...props} />,
              li: ({ node, ...props }) => <li style={{ marginBottom: '2px' }} {...props} />,
              strong: ({ node, children, ...props }) => (
                <strong style={{ fontWeight: 'bold', color: '#d63384', backgroundColor: 'rgba(214, 51, 132, 0.1)', padding: '0 4px', borderRadius: '2px' }} {...props}>
                  {children}
                </strong>
              ),
              em: ({ node, children, ...props }) => (
                <em style={{ fontStyle: 'italic', color: '#0066cc' }} {...props}>
                  {children}
                </em>
              ),
            }}
          >
            {item.details_markdown}
          </ReactMarkdown>
        </div>
      )}
      {item.subitems && item.subitems.length > 0 && (
        <div style={{ marginTop: '6px' }}>
          {item.subitems.map((subitem) => renderListItem(subitem, depth + 1))}
        </div>
      )}
    </div>
  );
};

const StructuredRenderer: React.FC<ContentRendererProps> = ({ content, className }) => {
  const data = useMemo(() => {
    try {
      const parsed = JSON.parse(content);

      // 如果已有 sections 字段，直接返回
      if (parsed && 'sections' in parsed && Array.isArray(parsed.sections)) {
        return parsed as StructuredContent;
      }

      // 如果是单个 section 对象，包装为 StructuredContent
      if (parsed && 'type' in parsed) {
        return {
          sections: [parsed as Section],
        } as StructuredContent;
      }

      return { sections: [] };
    } catch (e) {
      console.error('Failed to parse structured content:', e);
      return { sections: [] };
    }
  }, [content]);

  return (
    <div className={className} style={{ wordBreak: 'break-word', lineHeight: '1.4' }}>
      <style>{`
        .structured-content {
          line-height: 1.4;
        }
        .structured-content * {
          margin-top: 0;
          margin-bottom: 0;
        }
        .structured-content h1 {
          margin-bottom: 8px;
          margin-top: 12px;
          font-size: 24px;
          font-weight: bold;
        }
        .structured-content h2 {
          margin-bottom: 6px;
          margin-top: 10px;
          font-size: 20px;
          font-weight: bold;
        }
        .structured-content h3 {
          margin-bottom: 4px;
          margin-top: 8px;
          font-size: 18px;
          font-weight: bold;
        }
        .structured-content p {
          margin-bottom: 6px;
          margin-top: 4px;
          line-height: 1.5;
        }
        .structured-content ol,
        .structured-content ul {
          margin-bottom: 6px;
          margin-top: 4px;
          padding-left: 2em;
        }
        .structured-content ol ol,
        .structured-content ol ul,
        .structured-content ul ul,
        .structured-content ul ol {
          margin-top: 2px;
          margin-bottom: 2px;
        }
        .structured-content li {
          margin: 2px 0;
          line-height: 1.5;
        }
        .structured-content code {
          line-height: 1.4;
          background-color: #f0f0f0;
          padding: 2px 6px;
          border-radius: 3px;
          font-family: monospace;
          font-size: 0.9em;
          color: #d63384;
        }
        .structured-content pre {
          margin: 6px 0;
          line-height: 1.4;
          background-color: #f5f5f5;
          padding: 10px;
          border-radius: 4px;
          overflow: auto;
        }
        .structured-content table {
          border-collapse: collapse;
          margin: 6px 0;
          width: 100%;
        }
        .structured-content th {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
          font-weight: bold;
          background-color: #f5f5f5;
        }
        .structured-content td {
          border: 1px solid #ddd;
          padding: 8px;
        }
        .structured-content a {
          color: #1890ff;
          text-decoration: underline;
          cursor: pointer;
        }
        .structured-section {
          margin-bottom: 8px;
        }
        .structured-list-item {
          margin: 2px 0;
        }
      `}</style>

      <div className="structured-content">
        {data.sections && data.sections.length > 0 ? (
          data.sections.map((section, idx) => (
            <div key={idx} className="structured-section">
              {section.type === 'text' && (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ node, ...props }) => <h1 style={{ marginBottom: '12px', marginTop: '12px', fontSize: '24px', fontWeight: 'bold' }} {...props} />,
                    h2: ({ node, ...props }) => <h2 style={{ marginBottom: '10px', marginTop: '10px', fontSize: '20px', fontWeight: 'bold' }} {...props} />,
                    h3: ({ node, ...props }) => <h3 style={{ marginBottom: '8px', marginTop: '8px', fontSize: '18px', fontWeight: 'bold' }} {...props} />,
                    p: ({ node, ...props }) => <p style={{ marginBottom: '8px', lineHeight: '1.6' }} {...props} />,
                    ul: ({ node, ...props }) => <ul style={{ marginLeft: '2em', marginBottom: '8px', marginTop: '4px' }} {...props} />,
                    ol: ({ node, ...props }) => <ol style={{ marginLeft: '2em', marginBottom: '8px', marginTop: '4px' }} {...props} />,
                    li: ({ node, ...props }) => <li style={{ marginBottom: '4px', lineHeight: '1.4' }} {...props} />,
                    strong: ({ node, children, ...props }) => (
                      <strong style={{ fontWeight: 'bold', backgroundColor: 'transparent', padding: '0' }} {...props}>
                        {children}
                      </strong>
                    ),
                    em: ({ node, children, ...props }) => (
                      <em style={{ fontStyle: 'italic', color: '#0066cc' }} {...props}>
                        {children}
                      </em>
                    ),
                  }}
                >
                  {section.markdown}
                </ReactMarkdown>
              )}

              {section.type === 'list_ordered' && (
                <ol style={{ paddingLeft: '2em', margin: '4px 0 0' }}>
                  {section.items.map((item, i) => (
                    <li key={i} className="structured-list-item">
                      {renderListItem(item)}
                    </li>
                  ))}
                </ol>
              )}

              {section.type === 'list_unordered' && (
                <ul style={{ paddingLeft: '2em', margin: '4px 0 0' }}>
                  {section.items.map((item, i) => (
                    <li key={i} className="structured-list-item">
                      {renderListItem(item)}
                    </li>
                  ))}
                </ul>
              )}

              {section.type === 'code_block' && (
                <div style={{ margin: '6px 0' }}>
                  <div
                    style={{
                      backgroundColor: '#f5f5f5',
                      color: '#666',
                      fontSize: '12px',
                      padding: '4px 8px',
                      marginBottom: '4px',
                      borderRadius: '3px',
                    }}
                  >
                    {section.language}
                  </div>
                  <pre style={{ margin: '0', backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
                    <code style={{ fontFamily: 'monospace', fontSize: '13px', lineHeight: '1.4' }}>
                      {section.code}
                    </code>
                  </pre>
                </div>
              )}

              {section.type === 'table' && (
                <table style={{ borderCollapse: 'collapse', margin: '6px 0', width: '100%' }}>
                  <thead style={{ backgroundColor: '#f5f5f5' }}>
                    <tr>
                      {section.headers.map((header, i) => (
                        <th key={i} style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left', fontWeight: 'bold' }}>
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {section.rows.map((row, i) => (
                      <tr key={i}>
                        {row.map((cell, j) => (
                          <td key={j} style={{ border: '1px solid #ddd', padding: '8px' }}>
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          ))
        ) : (
          <div style={{ color: '#999' }}>No content to display</div>
        )}
      </div>
    </div>
  );
};

StructuredRenderer.displayName = 'StructuredRenderer';

export default StructuredRenderer;
