// Agent Observe MCP Type Definitions
// Following SPEC.md Section 4.3

export type Runtime = "browser" | "python";
export type ConsoleLevel = "log" | "error" | "warn" | "info" | "debug";

export interface ConsoleEntry {
  type: "console";
  runtime: Runtime;
  level: ConsoleLevel;
  timestamp: number;
  messages: string[];
  stack?: string;
  source: string;
  context: {
    url?: string;
    userAgent?: string;
  };
}

export interface NetworkEntry {
  type: "network";
  runtime: Runtime;
  id: string;
  method: string;
  url: string;
  path: string;
  domain: string;
  status: number;
  statusText: string;
  responseTime: number;
  requestHeaders: Record<string, string>;
  requestBody?: unknown;
  responseHeaders: Record<string, string>;
  responseBody?: unknown;
  validated: boolean;
  validationResult: {
    符合预期: boolean;
    原因?: string;
  };
  timestamp: number;
}

export interface ErrorEntry {
  message: string;
  stack: string;
  count: number;
  firstSeen: number;
  lastSeen: number;
}

export interface ErrorSummary {
  type: "error_summary";
  runtime: Runtime;
  errorCount: number;
  errors: ErrorEntry[];
  networkFailCount: number;
  networkFails: Array<{
    url: string;
    status: number;
    message: string;
  }>;
}

// --- Tool Input Types ---

export interface TimeRange {
  since?: number;   // Unix ms
  until?: number;
}

export interface ConsoleSnapshotArgs {
  runtime: Runtime;
  sessionId?: string;
  timeRange?: TimeRange;
  level?: ConsoleLevel;
}

export interface NetworkSnapshotArgs {
  runtime: Runtime;
  sessionId?: string;
  timeRange?: TimeRange;
  urlPattern?: string;
  status?: number;
}

export interface ErrorSummaryArgs {
  runtime: Runtime;
  sessionId?: string;
  timeRange?: TimeRange;
}

export interface ValidateResponseArgs {
  runtime: Runtime;
  sessionId?: string;
  expectedFields: string[];
  responseId?: string;
}

export interface CheckErrorsArgs {
  runtime: Runtime;
  sessionId?: string;
  expectedErrors: string[];
}

export interface AssertNetworkArgs {
  runtime: Runtime;
  sessionId?: string;
  url: string;
  expectedStatus: number;
}

export interface CollectAllArgs {
  runtime: Runtime;
  sessionId?: string;
  timeRange?: TimeRange;
}

export interface BrowserAttachArgs {
  url: string;
  cdpEndpoint?: string;
}

export interface BrowserDetachArgs {
  sessionId: string;
}

// --- Tool Result Types ---

export interface ConsoleSnapshotResult {
  entries: ConsoleEntry[];
  total: number;
  timeRange: { since: number; until: number };
}

export interface NetworkSnapshotResult {
  entries: NetworkEntry[];
  total: number;
  timeRange: { since: number; until: number };
}

export interface ErrorSummaryResult {
  summary: ErrorSummary;
  hasErrors: boolean;
  hasNetworkFails: boolean;
}

export interface ValidateResponseResult {
  responseId: string;
  validated: boolean;
  expectedFields: string[];
  presentFields: string[];
  missingFields: string[];
  extraFields: string[];
  detail: string;
}

export interface CheckErrorsResult {
  matched: boolean;
  matchedErrors: string[];
  unmatchedErrors: string[];
  foundErrors: ErrorEntry[];
}

export interface AssertNetworkResult {
  url: string;
  expectedStatus: number;
  actualStatus: number | null;
  matched: boolean;
  request?: NetworkEntry;
  detail: string;
}

export interface CollectAllResult {
  console: ConsoleEntry[];
  network: NetworkEntry[];
  errorSummary: ErrorSummary;
  stats: {
    consoleTotal: number;
    networkTotal: number;
    errorCount: number;
    networkFailCount: number;
  };
}

export interface BrowserAttachResult {
  sessionId: string;
  attachedUrl: string;
  cdpEndpoint?: string;
}

export interface BrowserDetachResult {
  sessionId: string;
  detached: boolean;
}
