import { FC } from 'react';
import TextRenderer from './TextRenderer';
import MarkdownRenderer from './MarkdownRenderer';
import HtmlRenderer from './HtmlRenderer';
import JsonRenderer from './JsonRenderer';
import StructuredRenderer from './StructuredRenderer';
import { ContentRendererProps, ContentType } from './types';

type RendererMap = {
  [key in ContentType]: FC<ContentRendererProps>;
};

const renderers: RendererMap = {
  text: TextRenderer,
  markdown: MarkdownRenderer,
  html: HtmlRenderer,
  json: JsonRenderer,
  structured: StructuredRenderer,
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
