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
      const customRenderer = () => ({ type: 'custom' });
      registerRenderer('text', customRenderer as any);
      const renderer = getContentRenderer('text');
      expect(renderer).toBe(customRenderer);
    });
  });
});
