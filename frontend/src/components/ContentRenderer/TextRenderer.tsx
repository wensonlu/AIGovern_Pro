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
