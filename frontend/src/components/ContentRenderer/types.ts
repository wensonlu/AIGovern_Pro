import { ReactNode } from 'react';

export type ContentType = 'text' | 'markdown' | 'html' | 'json' | 'structured';

export interface ContentRendererProps {
  content: string;
  className?: string;
}

export interface ContentRendererComponent {
  (props: ContentRendererProps): ReactNode;
  displayName?: string;
}
