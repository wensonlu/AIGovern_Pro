// Tests for Agent Observe MCP Tools
// Following SPEC.md - at least 6 unit tests

import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the runtimes before importing handlers
vi.mock("../src/runtimes/browser-runtime.js", () => ({
  browserRuntime: {
    getConsoleEntries: vi.fn(),
    getNetworkEntries: vi.fn(),
    clearBuffers: vi.fn(),
  },
}));

vi.mock("../src/runtimes/python-runtime.js", () => ({
  pythonRuntime: {
    getConsoleEntries: vi.fn(),
    getNetworkEntries: vi.fn(),
    getErrorSummary: vi.fn(),
  },
}));

import { browserRuntime } from "../src/runtimes/browser-runtime.js";
import { pythonRuntime } from "../src/runtimes/python-runtime.js";
import { handleConsoleSnapshot } from "../src/tools/console-snapshot.js";
import { handleNetworkSnapshot } from "../src/tools/network-snapshot.js";
import { handleErrorSummary } from "../src/tools/error-summary.js";
import { handleCheckErrors } from "../src/tools/check-errors.js";
import { handleAssertNetwork } from "../src/tools/assert-network.js";
import { handleValidateResponse } from "../src/tools/validate-response.js";
import { handleCollectAll } from "../src/tools/collect-all.js";
import type { ConsoleEntry, NetworkEntry } from "../src/types/index.js";

// --- Test Data Fixtures ---

const mockConsoleEntries: ConsoleEntry[] = [
  {
    type: "console",
    runtime: "browser",
    level: "log",
    timestamp: 1745884800000,
    messages: ["Hello World"],
    source: "http://example.com/index.html:10",
    context: { url: "http://example.com/index.html" },
  },
  {
    type: "console",
    runtime: "browser",
    level: "error",
    timestamp: 1745884801000,
    messages: ["TypeError: Cannot read property 'foo' of undefined"],
    stack: "TypeError: Cannot read property 'foo' of undefined\n    at bar (http://example.com/app.js:5)",
    source: "http://example.com/app.js:5",
    context: { url: "http://example.com/index.html" },
  },
];

const mockNetworkEntries: NetworkEntry[] = [
  {
    type: "network",
    runtime: "browser",
    id: "http://example.com/api/users",
    method: "GET",
    url: "http://example.com/api/users",
    path: "/api/users",
    domain: "example.com",
    status: 200,
    statusText: "OK",
    responseTime: 150,
    requestHeaders: { "Content-Type": "application/json" },
    responseHeaders: { "Content-Type": "application/json" },
    responseBody: { users: [{ id: 1, name: "Alice" }] },
    validated: false,
    validationResult: { 符合预期: false },
    timestamp: 1745884802000,
  },
  {
    type: "network",
    runtime: "browser",
    id: "http://example.com/api/users/1",
    method: "GET",
    url: "http://example.com/api/users/1",
    path: "/api/users/1",
    domain: "example.com",
    status: 404,
    statusText: "Not Found",
    responseTime: 80,
    requestHeaders: {},
    responseHeaders: {},
    responseBody: null,
    validated: false,
    validationResult: { 符合预期: false },
    timestamp: 1745884803000,
  },
];

// --- Tests ---

describe("debug_console_snapshot", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return browser console entries", async () => {
    vi.mocked(browserRuntime.getConsoleEntries).mockReturnValue([...mockConsoleEntries]);
    
    const result = await handleConsoleSnapshot({ runtime: "browser" });
    
    expect(result.total).toBe(2);
    expect(result.entries).toHaveLength(2);
    expect(result.entries[0].level).toBe("log");
  });

  it("should return python console entries", async () => {
    vi.mocked(pythonRuntime.getConsoleEntries).mockResolvedValue([mockConsoleEntries[0]]);
    
    const result = await handleConsoleSnapshot({ runtime: "python" });
    
    expect(result.total).toBe(1);
  });

  it("should filter entries by level", async () => {
    vi.mocked(browserRuntime.getConsoleEntries).mockReturnValue([...mockConsoleEntries]);
    
    const result = await handleConsoleSnapshot({ runtime: "browser", level: "error" });
    
    expect(result.total).toBe(1);
    expect(result.entries[0].level).toBe("error");
  });

  it("should filter entries by time range", async () => {
    vi.mocked(browserRuntime.getConsoleEntries).mockReturnValue([...mockConsoleEntries]);
    
    const result = await handleConsoleSnapshot({
      runtime: "browser",
      timeRange: { since: 1745884800500, until: 1745884802000 },
    });
    
    expect(result.total).toBe(1);
    expect(result.entries[0].messages).toEqual(["TypeError: Cannot read property 'foo' of undefined"]);
  });
});

describe("debug_network_snapshot", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return browser network entries", async () => {
    vi.mocked(browserRuntime.getNetworkEntries).mockReturnValue([...mockNetworkEntries]);
    
    const result = await handleNetworkSnapshot({ runtime: "browser" });
    
    expect(result.total).toBe(2);
  });

  it("should filter by URL pattern", async () => {
    vi.mocked(browserRuntime.getNetworkEntries).mockReturnValue([...mockNetworkEntries]);
    
    const result = await handleNetworkSnapshot({
      runtime: "browser",
      urlPattern: "/api/users/*",
    });
    
    expect(result.total).toBe(1);
    expect(result.entries[0].url).toBe("http://example.com/api/users/1");
  });

  it("should filter by status code", async () => {
    vi.mocked(browserRuntime.getNetworkEntries).mockReturnValue([...mockNetworkEntries]);
    
    const result = await handleNetworkSnapshot({
      runtime: "browser",
      status: 404,
    });
    
    expect(result.total).toBe(1);
    expect(result.entries[0].status).toBe(404);
  });
});

describe("debug_error_summary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should summarize errors and network failures", async () => {
    vi.mocked(browserRuntime.getConsoleEntries).mockReturnValue([...mockConsoleEntries]);
    vi.mocked(browserRuntime.getNetworkEntries).mockReturnValue([...mockNetworkEntries]);
    
    const result = await handleErrorSummary({ runtime: "browser" });
    
    expect(result.hasErrors).toBe(true);
    expect(result.hasNetworkFails).toBe(true);
    expect(result.summary.errorCount).toBe(1);
    expect(result.summary.networkFailCount).toBe(1);
  });

  it("should return empty summary when no errors", async () => {
    vi.mocked(browserRuntime.getConsoleEntries).mockReturnValue([mockConsoleEntries[0]]);
    vi.mocked(browserRuntime.getNetworkEntries).mockReturnValue([mockNetworkEntries[0]]);
    
    const result = await handleErrorSummary({ runtime: "browser" });
    
    expect(result.hasErrors).toBe(false);
    expect(result.hasNetworkFails).toBe(false);
  });
});

describe("debug_check_errors", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should find matching error patterns", async () => {
    vi.mocked(browserRuntime.getConsoleEntries).mockReturnValue([mockConsoleEntries[1]]);
    
    const result = await handleCheckErrors({
      runtime: "browser",
      expectedErrors: ["TypeError", "Cannot read"],
    });
    
    expect(result.matched).toBe(true);
    expect(result.matchedErrors).toEqual(["TypeError", "Cannot read"]);
    expect(result.unmatchedErrors).toHaveLength(0);
  });

  it("should report unmatched patterns", async () => {
    vi.mocked(browserRuntime.getConsoleEntries).mockReturnValue([mockConsoleEntries[1]]);
    
    const result = await handleCheckErrors({
      runtime: "browser",
      expectedErrors: ["NetworkError", "Timeout"],
    });
    
    expect(result.matched).toBe(false);
    expect(result.matchedErrors).toHaveLength(0);
    expect(result.unmatchedErrors).toEqual(["NetworkError", "Timeout"]);
  });
});

describe("debug_assert_network", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should match successful network request", async () => {
    vi.mocked(browserRuntime.getNetworkEntries).mockReturnValue([...mockNetworkEntries]);
    
    const result = await handleAssertNetwork({
      runtime: "browser",
      url: "/api/users",
      expectedStatus: 200,
    });
    
    expect(result.matched).toBe(true);
    expect(result.actualStatus).toBe(200);
  });

  it("should detect status mismatch", async () => {
    vi.mocked(browserRuntime.getNetworkEntries).mockReturnValue([...mockNetworkEntries]);
    
    const result = await handleAssertNetwork({
      runtime: "browser",
      url: "/api/users/1",
      expectedStatus: 200,
    });
    
    expect(result.matched).toBe(false);
    expect(result.actualStatus).toBe(404);
  });

  it("should handle no matching URL", async () => {
    vi.mocked(browserRuntime.getNetworkEntries).mockReturnValue([...mockNetworkEntries]);
    
    const result = await handleAssertNetwork({
      runtime: "browser",
      url: "/nonexistent",
      expectedStatus: 200,
    });
    
    expect(result.matched).toBe(false);
    expect(result.actualStatus).toBeNull();
  });
});

describe("debug_validate_response", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should validate present fields", async () => {
    vi.mocked(browserRuntime.getNetworkEntries).mockReturnValue([...mockNetworkEntries]);
    
    const result = await handleValidateResponse({
      runtime: "browser",
      expectedFields: ["users"],
    });
    
    expect(result.validated).toBe(true);
    expect(result.missingFields).toHaveLength(0);
  });

  it("should report missing fields", async () => {
    vi.mocked(browserRuntime.getNetworkEntries).mockReturnValue([...mockNetworkEntries]);
    
    const result = await handleValidateResponse({
      runtime: "browser",
      expectedFields: ["users", "total", "page"],
    });
    
    expect(result.validated).toBe(false);
    expect(result.missingFields).toContain("total");
    expect(result.missingFields).toContain("page");
  });
});