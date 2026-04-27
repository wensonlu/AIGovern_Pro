/**
 * API 服务层 - 增强版
 * 与后端 FastAPI 通信，支持重试、超时、日志
 */

// API 响应类型定义
export interface HealthResponse {
  status: string;
}

export interface SourceReference {
  document_id?: number | string;
  title: string;
  filename?: string;
  chunk_index?: number;
  relevance: number;
  relevance_percentage: string;
  text_preview?: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceReference[];
  confidence: number;
  session_id?: string;
  timestamp?: string;
}

export type ChatStreamEvent =
  | {
      type: 'format';
      content_type: 'text' | 'markdown' | 'html' | 'json';
    }
  | {
      type: 'sources';
      sources: SourceReference[];
      confidence: number;
      session_id?: string;
    }
  | {
      type: 'section';
      section: {
        type: 'text' | 'list_ordered' | 'list_unordered' | 'code_block' | 'table';
        markdown?: string;
        items?: any[];
        language?: string;
        code?: string;
        headers?: string[];
        rows?: string[][];
      };
    }
  | {
      type: 'debug';
      llm_output: string;
    }
  | {
      type: 'delta';
      content: string;
    }
  | {
      type: 'done';
      confidence: number;
      session_id?: string;
      timestamp?: string;
    }
  | {
      type: 'error';
      message: string;
    };

export interface ChatStreamHandlers {
  onSources?: (event: Extract<ChatStreamEvent, { type: 'sources' }>) => void;
  onSection?: (section: any) => void;
  onDelta?: (content: string) => void;
  onDone?: (event: Extract<ChatStreamEvent, { type: 'done' }>) => void;
}

export interface QueryResponse {
  sql: string;
  result: Array<Record<string, any>>;
  chart_type: string;
}

export interface OperationTemplate {
  id: string;
  name: string;
  description: string;
  parameters: Record<string, any>;
}

export interface OperationResponse {
  status: string;
  result?: Record<string, any>;
  error?: string;
}

export interface DiagnosisSummaryResponse {
  summary: string;
  key_findings: string[];
}

export interface MetricsResponse {
  metrics: Array<{
    name: string;
    value: number;
    unit: string;
  }>;
}

export interface AnalysisResponse {
  metric_name: string;
  analysis: string;
  recommendations: string[];
}

// API 基础地址
// 默认走同源相对路径，开发环境交给 Vite proxy 转发，避免浏览器跨域。
// 如确需直连后端，可通过 VITE_API_URL 显式覆盖。
const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const API_TIMEOUT = import.meta.env.VITE_API_TIMEOUT || 30000;
const MAX_RETRIES = 3;

// 延迟函数
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// 判断是否应该重试
function shouldRetry(error: any): boolean {
  if (error instanceof TypeError) return true; // 网络错误
  if (error.name === 'AbortError') return true; // 超时
  return false;
}

// 带重试机制的 fetch 包装
async function fetchWithRetry(
  url: string,
  options: RequestInit,
  retries: number = 0
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (retries < MAX_RETRIES && shouldRetry(error)) {
      const backoff = 1000 * Math.pow(2, retries); // 指数退避
      console.warn(`[API重试] ${url} (${retries + 1}/${MAX_RETRIES}) 等待${backoff}ms...`);
      await delay(backoff);
      return fetchWithRetry(url, options, retries + 1);
    }
    throw error;
  }
}

// 统一的 API 调用包装函数
async function callAPI<T>(
  endpoint: string,
  method: 'GET' | 'POST' = 'GET',
  body?: any
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const startTime = Date.now();

  if (!import.meta.env.PROD) {
    console.log(`[API] ${method} ${endpoint}`, body ? `(payload: ${JSON.stringify(body).slice(0, 100)}...)` : '');
  }

  try {
    const response = await fetchWithRetry(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });

    const data = await response.json();
    const duration = Date.now() - startTime;
    if (!import.meta.env.PROD) {
      console.log(`[API✓] ${method} ${endpoint} (${duration}ms)`);
    }

    return data as T;
  } catch (error) {
    const duration = Date.now() - startTime;
    if (!import.meta.env.PROD) {
      console.error(`[API✗] ${method} ${endpoint} (${duration}ms):`, error);
    }
    throw error;
  }
}

// 健康检查
export async function checkHealth(): Promise<HealthResponse> {
  return callAPI<HealthResponse>('/health', 'GET');
}

// 知识问答 API
export async function chatWithKnowledge(
  question: string,
  sessionId: string = 'default',
  topK: number = 5
): Promise<ChatResponse> {
  return callAPI<ChatResponse>('/api/chat', 'POST', {
    question,
    session_id: sessionId,
    top_k: topK,
  });
}

// 知识问答流式 API
export async function streamChatWithKnowledge(
  question: string,
  sessionId: string = 'default',
  topK: number = 5,
  handlers: ChatStreamHandlers = {},
  useStructured: boolean = true  // 默认使用新的结构化 API
): Promise<ChatResponse> {
  // 优先使用结构化 API，降级到旧 API
  const endpoint = useStructured ? '/api/chat/structured/stream' : '/api/chat/stream';

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      session_id: sessionId,
      top_k: topK,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  if (!response.body) {
    throw new Error('浏览器不支持流式响应');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let answer = '';
  let sources: SourceReference[] = [];
  let confidence = 0;
  let timestamp: string | undefined;
  let sections: any[] = [];  // 结构化输出的 sections

  const consumeLine = (line: string) => {
    if (!line.trim()) return;

    const event = JSON.parse(line) as ChatStreamEvent;

    if (event.type === 'format') {
      // 格式事件 - 前端可根据content_type选择渲染器
      return;
    }

    if (event.type === 'sources') {
      sources = event.sources || [];
      confidence = event.confidence || 0;
      handlers.onSources?.(event);
      return;
    }

    // 处理结构化 API 的 section 事件
    if (event.type === 'section') {
      const section = event.section;
      if (section) {
        sections.push(section);
        // 将结构化的 section 返回给 handler
        handlers.onSection?.(section);
      }
      return;
    }

    // 调试事件 - 原始 LLM 输出（不使用）
    if (event.type === 'debug') {
      return;
    }

    if (event.type === 'delta') {
      answer += event.content;
      handlers.onDelta?.(event.content);
      return;
    }

    if (event.type === 'done') {
      confidence = event.confidence ?? confidence;
      timestamp = event.timestamp;
      handlers.onDone?.(event);
      return;
    }

    if (event.type === 'error') {
      throw new Error(event.message);
    }
  };

  let isReading = true;
  while (isReading) {
    const { done, value } = await reader.read();
    if (done) {
      isReading = false;
      continue;
    }

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    lines.forEach(consumeLine);
  }

  buffer += decoder.decode();
  consumeLine(buffer);

  return {
    answer,
    sources,
    confidence,
    session_id: sessionId,
    timestamp,
  };
}

// 数据查询 API
export async function queryData(naturalLanguageQuery: string): Promise<QueryResponse> {
  return callAPI<QueryResponse>('/api/query', 'POST', {
    natural_language_query: naturalLanguageQuery,
  });
}

// 获取操作模板列表
export async function getOperationTemplates(): Promise<OperationTemplate[]> {
  return callAPI<OperationTemplate[]>('/api/operations/templates', 'GET');
}

// 执行操作
export async function executeOperation(
  operationType: string,
  parameters: Record<string, any>
): Promise<OperationResponse> {
  return callAPI<OperationResponse>(`/api/operations/${operationType}/execute`, 'POST', {
    operation_type: operationType,
    parameters,
  });
}

// 获取诊断总结
export async function getDiagnosisSummary(): Promise<DiagnosisSummaryResponse> {
  return callAPI<DiagnosisSummaryResponse>('/api/diagnosis/summary', 'GET');
}

// 获取诊断指标
export async function getDiagnosisMetrics(): Promise<MetricsResponse> {
  return callAPI<MetricsResponse>('/api/diagnosis/metrics', 'GET');
}

// 深度分析诊断指标
export async function analyzeDiagnosisMetric(metricName: string): Promise<AnalysisResponse> {
  return callAPI<AnalysisResponse>(`/api/diagnosis/analyze/${metricName}`, 'GET');
}

export default {
  checkHealth,
  chatWithKnowledge,
  streamChatWithKnowledge,
  queryData,
  getOperationTemplates,
  executeOperation,
  getDiagnosisSummary,
  getDiagnosisMetrics,
  analyzeDiagnosisMetric,
};
