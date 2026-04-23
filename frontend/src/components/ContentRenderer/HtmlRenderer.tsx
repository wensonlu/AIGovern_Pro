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
