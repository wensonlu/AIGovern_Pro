# AIGovern_Pro - Agent Observe MCP 技术规格文档

> 项目：企业 AI 管理系统  
> 创建时间：2026-04-29  
> 状态：**技术规格确认中（待最终确认后进入实现）**

---

## 一、背景与目标

AIGovern_Pro 是企业级 AI Agent 管理平台，本次迭代为 AI Agent 提供生产级代码调试能力：

- 集成浏览器 DevTools Protocol 和 Python Runtime 的 console + network 监控
- AI 主动调用，返回结构化数据（Method A · Structured Data）
- 所有报错和接口返回均可按需求校验并输出结果

---

## 二、项目结构

```
AIGovern_Pro/
├── agent-observe-mcp/              # Agent Observe MCP（本期 P0）
│   ├── src/
│   │   ├── index.ts            # MCP Server 入口
│   │   ├── tools/              # 7 个 MCP 工具实现
│   │   │   ├── console-snapshot.ts
│   │   │   ├── network-snapshot.ts
│   │   │   ├── error-summary.ts
│   │   │   ├── validate-response.ts
│   │   │   ├── check-errors.ts
│   │   │   ├── assert-network.ts
│   │   │   └── collect-all.ts
│   │   ├── runtimes/           # 运行时适配器
│   │   │   ├── browser-runtime.ts   # Playwright CDP
│   │   │   └── python-runtime.ts    # Python SDK 集成
│   │   ├── types/              # 类型定义
│   │   │   └── index.ts
│   │   └── lib/                # 公共工具
│   │       ├── logger.ts
│   │       └── validator.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── vitest.config.ts
├── python-sdk/                 # Python Runtime SDK（本期 P0）
│   ├── ai_debug_sdk/
│   │   ├── __init__.py
│   │   ├── console_hook.py     # print/logging hook
│   │   ├── network_hook.py     # httpx/requests hook
│   │   └── collector.py        # 数据收集器
│   ├── pyproject.toml
│   └── tests/
├── ops-mcp/                   # 运营 MCP（二期待实现）
└── SPEC.md                    # 本文档
```

---

## 三、技术选型决策

### 3.1 技术调研背景

在确定最终方案前，对以下两个关键问题进行了深度技术调研：

---

### 3.2 问题一：Python 集成方式

#### 方案对比

| 维度 | A. import SDK 引入 | B. 启动参数注入 |
|------|-------------------|----------------|
| 接入成本 | 低（加一行 import） | 高（改启动命令） |
| 源码侵入 | 无 | 无 |
| 配置灵活度 | 高（代码内可控制） | 低（参数传递麻烦） |
| CI/CD 兼容性 | ✅ 好 | ⚠️ 需改脚本 |
| 适用场景 | 自己的脚本 | 第三方/无源码脚本 |

#### 结论：选择 **方案 A · `import ai_debug_sdk` 直接引入**

**理由：**
1. 接入成本最低，改动最小
2. 配置灵活（enable/disable、按需开关）
3. AI Agent 调用的 Python 脚本通常是自己写的，有源码
4. CI/CD 场景下只需在测试脚本开头加 import

---

### 3.3 问题二：浏览器自动化框架

#### 方案对比

| 维度 | A. Playwright | B. Puppeteer |
|------|-------------|-------------|
| 跨语言支持 | ✅ Python/Node.js/Java/C# | ❌ 仅 Node.js |
| 浏览器覆盖 | Chromium/Firefox/WebKit | 仅 Chromium |
| CDP 支持 | 完整（console/network 全覆盖） | 最完整（Google 亲儿子） |
| 包体积 | 较大（~200MB） | 较小（~50MB） |
| API 设计 | 现代，Promise 原生 | 较老 |
| 文档质量 | 清晰，示例丰富 | 清晰 |
| 本期场景适用 | ✅ 完美 | ⚠️ 够用但不跨语言 |

#### 结论：选择 **方案 A · Playwright**

**理由：**
1. TypeScript/Node.js 实现首选，API 现代
2. CDP 会话完整，可获取 console + network 全量数据
3. 未来 Python SDK 如需浏览器能力，可复用同一套思路
4. 跨浏览器支持预留（测试场景 Firefox/WebKit 可能有用）

---

## 四、Agent Observe MCP 详细设计（本期 P0）

### 4.1 技术栈

| 层级 | 技术选型 |
|------|---------|
| 语言 | TypeScript 5.x |
| 运行时 | Node.js 20+ |
| MCP 协议 | @modelcontextprotocol/sdk（stdio 模式） |
| 浏览器自动化 | Playwright 1.x |
| Python SDK | Python 3.10+，httpx + logging |

### 4.2 MCP Server 入口设计

```typescript
// src/index.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { createConsoleSnapshotTool } from "./tools/console-snapshot.js";
import { createNetworkSnapshotTool } from "./tools/network-snapshot.js";
import { createErrorSummaryTool } from "./tools/error-summary.js";
import { createValidateResponseTool } from "./tools/validate-response.js";
import { createCheckErrorsTool } from "./tools/check-errors.js";
import { createAssertNetworkTool } from "./tools/assert-network.js";
import { createCollectAllTool } from "./tools/collect-all.js";

const server = new Server(
  { name: "agent-observe-mcp", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

// 注册全部 7 个工具
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    createConsoleSnapshotTool(),
    createNetworkSnapshotTool(),
    createErrorSummaryTool(),
    createValidateResponseTool(),
    createCheckErrorsTool(),
    createAssertNetworkTool(),
    createCollectAllTool(),
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  // 路由到对应工具...
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### 4.3 数据类型定义

```typescript
// src/types/index.ts

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

// --- 工具入参类型 ---

export interface TimeRange {
  since?: number;   // Unix ms
  until?: number;
}

export interface ConsoleSnapshotArgs {
  runtime: Runtime;
  timeRange?: TimeRange;
  level?: ConsoleLevel;
}

export interface NetworkSnapshotArgs {
  runtime: Runtime;
  timeRange?: TimeRange;
  urlPattern?: string;
  status?: number;
}

export interface ErrorSummaryArgs {
  runtime: Runtime;
  timeRange?: TimeRange;
}

export interface ValidateResponseArgs {
  runtime: Runtime;
  expectedFields: string[];
  responseId?: string;
}

export interface CheckErrorsArgs {
  runtime: Runtime;
  expectedErrors: string[];
}

export interface AssertNetworkArgs {
  runtime: Runtime;
  url: string;
  expectedStatus: number;
}

export interface CollectAllArgs {
  runtime: Runtime;
  timeRange?: TimeRange;
}
```

### 4.4 工具接口签名

#### 4.4.1 `debug_console_snapshot`

```typescript
// 入参
interface ConsoleSnapshotArgs {
  runtime: "browser" | "python";
  timeRange?: { since?: number; until?: number };
  level?: "log" | "error" | "warn" | "info" | "debug";
}

// 返回
interface ConsoleSnapshotResult {
  entries: ConsoleEntry[];
  total: number;
  timeRange: { since: number; until: number };
}
```

#### 4.4.2 `debug_network_snapshot`

```typescript
// 入参
interface NetworkSnapshotArgs {
  runtime: "browser" | "python";
  timeRange?: { since?: number; until?: number };
  urlPattern?: string;  // 支持 * wildcard，如 "/api/v1/*"
  status?: number;
}

// 返回
interface NetworkSnapshotResult {
  entries: NetworkEntry[];
  total: number;
  timeRange: { since: number; until: number };
}
```

#### 4.4.3 `debug_error_summary`

```typescript
// 入参
interface ErrorSummaryArgs {
  runtime: "browser" | "python";
  timeRange?: { since?: number; until?: number };
}

// 返回
interface ErrorSummaryResult {
  summary: ErrorSummary;
  hasErrors: boolean;
  hasNetworkFails: boolean;
}
```

#### 4.4.4 `debug_validate_response`

```typescript
// 入参
interface ValidateResponseArgs {
  runtime: "browser" | "python";
  expectedFields: string[];  // 如 ["token", "userId", "expiresAt"]
  responseId?: string;         // 不填则取最新一个
}

// 返回
interface ValidateResponseResult {
  responseId: string;
  validated: boolean;
  expectedFields: string[];
  presentFields: string[];
  missingFields: string[];
  extraFields: string[];
  detail: string;
}
```

#### 4.4.5 `debug_check_errors`

```typescript
// 入参
interface CheckErrorsArgs {
  runtime: "browser" | "python";
  expectedErrors: string[];  // 关键词列表，如 ["TypeError", "Cannot read"]
}

// 返回
interface CheckErrorsResult {
  matched: boolean;
  matchedErrors: string[];   // 匹配到的 expectedErrors
  unmatchedErrors: string[]; // 未匹配到的 expectedErrors
  foundErrors: ErrorEntry[];
}
```

#### 4.4.6 `debug_assert_network`

```typescript
// 入参
interface AssertNetworkArgs {
  runtime: "browser" | "python";
  url: string;               // 精确 URL 或带 * 的 pattern
  expectedStatus: number;    // 期望的 HTTP 状态码
}

// 返回
interface AssertNetworkResult {
  url: string;
  expectedStatus: number;
  actualStatus: number | null;
  matched: boolean;
  request?: NetworkEntry;
  detail: string;
}
```

#### 4.4.7 `debug_collect_all`

```typescript
// 入参
interface CollectAllArgs {
  runtime: "browser" | "python";
  timeRange?: { since?: number; until?: number };
}

// 返回
interface CollectAllResult {
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
```

### 4.5 浏览器 Runtime 适配器（Playwright CDP）

```typescript
// src/runtimes/browser-runtime.ts
import { chromium, Browser, CDPSession, ConsoleMessage } from "playwright";
import { ConsoleEntry, NetworkEntry } from "../types/index.js";

export class BrowserRuntime {
  private browser: Browser | null = null;
  private consoleBuffer: ConsoleEntry[] = [];
  private networkBuffer: NetworkEntry[] = [];

  async launch(): Promise<void> {
    this.browser = await chromium.launch({
      args: ["--remote-debugging-port=9222"],
    });
  }

  async attach(url: string): Promise<void> {
    if (!this.browser) throw new Error("Browser not launched");
    const context = await this.browser.newContext();
    const page = await context.newPage();

    // Console 监听
    page.on("console", (msg: ConsoleMessage) => {
      this.consoleBuffer.push({
        type: "console",
        runtime: "browser",
        level: msg.type() as ConsoleEntry["level"],
        timestamp: Date.now(),
        messages: msg.args().map((a) => a.toString()),
        source: `${msg.location().url}:${msg.location().lineNumber}`,
        context: { url: page.url() },
      });
    });

    // Network 监听
    page.on("response", async (response) => {
      const req = response.request();
      this.networkBuffer.push({
        type: "network",
        runtime: "browser",
        id: req.url(),
        method: req.method(),
        url: response.url(),
        path: new URL(response.url()).pathname,
        domain: new URL(response.url()).hostname,
        status: response.status(),
        statusText: response.statusText(),
        responseTime: response.timing()?.responseStart
          ? response.timing().responseStart - response.timing().requestStart
          : 0,
        requestHeaders: req.headers(),
        requestBody: req.postDataBuffer()?.toString(),
        responseHeaders: response.headers(),
        responseBody: await response.text().catch(() => undefined),
        validated: false,
        validationResult: { 符合预期: false },
        timestamp: Date.now(),
      });
    });

    await page.goto(url);
  }

  getConsoleEntries(): ConsoleEntry[] {
    return [...this.consoleBuffer];
  }

  getNetworkEntries(): NetworkEntry[] {
    return [...this.networkBuffer];
  }

  async close(): Promise<void> {
    await this.browser?.close();
  }
}
```

### 4.6 Python Runtime SDK 设计

```
python-sdk/
├── ai_debug_sdk/
│   ├── __init__.py      # 导出 enable/disable 和收集函数
│   ├── console_hook.py  # print + logging hook
│   ├── network_hook.py  # httpx + requests hook
│   └── collector.py     # 共享数据收集器（HTTP Server）
└── pyproject.toml
```

#### `__init__.py` 核心接口

```python
# ai_debug_sdk/__init__.py
from .console_hook import ConsoleHook
from .network_hook import NetworkHook
from .collector import Collector

_collector = Collector()
_console_hook = ConsoleHook(_collector)
_network_hook = NetworkHook(_collector)

def enable():
    """开启全局监控（import 时自动调用）"""
    _console_hook.install()
    _network_hook.install()

def disable():
    """关闭监控"""
    _console_hook.uninstall()
    _network_hook.uninstall()

def get_console_entries(since: int | None = None) -> list[dict]:
    """获取 console 日志"""
    return _collector.get_console(since=since)

def get_network_entries(since: int | None = None) -> list[dict]:
    """获取网络请求"""
    return _collector.get_network(since=since)

def clear():
    """清空缓冲区"""
    _collector.clear()
```

#### HTTP Server 模式（供 MCP Server 调用）

```python
# ai_debug_sdk/collector.py
from http.server import HTTPServer
from threading import Thread
import json

class Collector:
    def __init__(self, port: int = 9310):
        self._port = port
        self._console: list[dict] = []
        self._network: list[dict] = []
        self._server = None
        self._thread = None

    def start(self):
        """启动 HTTP API Server，MCP Server 通过 HTTP 调用获取数据"""
        self._server = HTTPServer(("127.0.0.1", self._port), self._handler)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def add_console(self, entry: dict):
        self._console.append(entry)

    def add_network(self, entry: dict):
        self._network.append(entry)

    def get_console(self, since: int | None = None) -> list[dict]:
        if since is None:
            return self._console
        return [e for e in self._console if e["timestamp"] > since]

    def get_network(self, since: int | None = None) -> list[dict]:
        if since is None:
            return self._network
        return [e for e in self._network if e["timestamp"] > since]

    def clear(self):
        self._console.clear()
        self._network.clear()
```

### 4.7 Python 集成方式

```python
# 方式：直接 import（推荐）
import ai_debug_sdk  # 开启全局监控

# 正常使用业务代码
import requests
import logging

logging.basicConfig(level=logging.INFO)

response = requests.get("https://api.example.com/users")
print("请求完成:", response.status_code)

# AI Agent 通过 HTTP API 查询监控数据
# GET http://127.0.0.1:9310/console?since=1745884800000
# GET http://127.0.0.1:9310/network?since=1745884800000
```

MCP Server 通过 `http://127.0.0.1:9310` 调用 Python SDK 获取数据，无需直接操作 Python 进程。

---

## 五、运营 MCP（二期待实现）

### 5.1 核心定位

| 项目 | 说明 |
|------|------|
| 目标用户 | 运营人员（非 AI Agent） |
| 定位 | 日常 AI 系统运维和业务数据查询 |
| 阶段 | 二期 P1 |

### 5.2 待确认问题

- [ ] 运营人员日常最高频的 3 个操作是什么？
- [ ] 需要查询哪些数据？（AI 调用记录？Token 消耗？业务数据？）
- [ ] 是否需要审批/审核能力？
- [ ] 使用入口？（Web UI / Bot / API）

### 5.3 占位工具清单（待填充）

| 工具名（暂定） | 入参 | 返回 |
|----------------|------|------|
| `ops_query_sessions` | dateRange?, userId? | AI 会话记录列表 |
| `ops_query_usage` | dateRange?, aggregation? | Token 消耗统计 |
| `ops_alert_list` | status?, priority? | 告警列表 |
| `ops_audit_logs` | operator?, action? | 操作审计日志 |

---

## 六、方案 B · Live Object（二期储备）

> 以下为二期能力设计，方案 A 稳定后启动

**核心思路**：建立 session 管理，AI 持续监控并主动查询累积数据

```
sessionId = debug_monitor_start(runtime, events)
debug_monitor_query(sessionId, filter, limit)
debug_on_error(sessionId, callback)
debug_monitor_stop(sessionId)
```

**技术要求**：WebSocket/SSE 实时推送 + session TTL 管理

---

## 七、阶段规划

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| **本期** | Agent Observe MCP（方案 A）全工具实现 | P0 |
| **本期** | Python Runtime SDK（console + network hook） | P0 |
| **本期** | 浏览器 CDP 集成（Playwright） | P0 |
| **二期** | Agent Observe MCP（方案 B）session 管理 | P1 |
| **二期** | 运营 MCP 工具实现 | P1 |
| **三期** | Web UI 管理后台 | P2 |

---

## 八、技术约束汇总

| 约束项 | 要求 |
|--------|------|
| MCP Server 语言 | TypeScript 5.x |
| MCP Server 运行时 | Node.js 20+ |
| MCP 协议入口 | @modelcontextprotocol/sdk（StdioServerTransport） |
| 浏览器自动化 | Playwright 1.x |
| Python 版本 | Python 3.10+ |
| Python HTTP Client | httpx + requests |
| Python SDK 通信 | HTTP Server（port 9310） |
| 输出格式 | 统一 JSON |
| 鉴权 | MCP 调用方携带有效 token |
| 响应时间 | 快照类 < 2s |
| 数据保留 | console/network 日志服务端保留 7 天 |
| Python SDK 侵入性 | 极低（仅一行 import） |
| 测试框架 | Vitest |

---

## 九、待确认事项

| 序号 | 事项 | 状态 |
|------|------|------|
| 1 | Python 集成方式 | ✅ 已确认：方案 A（import SDK） |
| 2 | 浏览器自动化框架 | ✅ 已确认：Playwright |
| 3 | 运营 MCP 具体场景和工具需求 | ⏳ 待确认（二期待定） |
| 4 | CI/CD 集成需求（Jenkins/GitHub Actions） | ⏳ 待确认 |
