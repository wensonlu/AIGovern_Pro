# 验收用例数据结构设计

本文档定义 AI 自主验收系统的核心数据模型，包括用例生成、测试执行、结果记录等数据结构。

## 一、核心实体关系

```
┌─────────────────────────────────────────────────────────────────────┐
│                         核心实体关系图                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Project (项目)                                                     │
│       │                                                             │
│       ├─1─► Feature (功能)                                         │
│       │       │                                                     │
│       │       ├─1─► AcceptanceTest (验收用例) ──────┐             │
│       │       │       │                             │             │
│       │       │       ├─1─► TestStep (测试步骤)     │             │
│       │       │       │                             │             │
│       │       │       ├─1─► Assertion (断言)        │             │
│       │       │       │                             │             │
│       │       │       └─n─► TestRun (测试执行) ─────┤             │
│       │       │                                     │             │
│       │       └─n─► FailureCase (失败案例)          │             │
│       │                                                 │             │
│       └─n─► TestRun (测试执行)                        │             │
│             │                                          │             │
│             └─n─► TestResult (测试结果) ◄────────────┘             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 二、核心数据结构

### 2.1 项目 (Project)

```typescript
interface Project {
  id: string;                    // 项目ID
  name: string;                  // 项目名称
  type: ProjectType;             // 项目类型
  repoUrl: string;               // Git 仓库地址
  framework: string;            // 技术栈
  createdAt: Date;              // 创建时间
  updatedAt: Date;              // 更新时间
  settings: ProjectSettings;    // 项目配置
}

type ProjectType = 'FRONTEND' | 'BACKEND' | 'FULLSTACK' | 'MOBILE';

interface ProjectSettings {
  buildCommand: string;         // 构建命令
  testCommand: string;          // 测试命令
  baseUrl: string;              // 基础 URL
  ignorePaths: string[];       // 忽略路径
  timeout: number;              // 超时时间(ms)
  retryCount: number;           // 重试次数
}
```

### 2.2 功能 (Feature)

```typescript
interface Feature {
  id: string;                    // 功能ID
  projectId: string;            // 所属项目ID
  name: string;                 // 功能名称
  description: string;          // 功能描述
  requirementDoc: string;       // 需求文档链接
  priority: Priority;           // 优先级
  status: FeatureStatus;        // 状态
  createdAt: Date;
  updatedAt: Date;
}

type Priority = 'P0' | 'P1' | 'P2' | 'P3';
type FeatureStatus = 'DRAFT' | 'IN_PROGRESS' | 'TESTING' | 'COMPLETED' | 'ARCHIVED';
```

### 2.3 验收用例 (AcceptanceTest)

```typescript
interface AcceptanceTest {
  id: string;                    // 用例ID
  featureId: string;            // 所属功能ID
  name: string;                 // 用例名称
  description: string;          // 用例描述
  
  // 用例分类
  testType: TestType;           // 验收类型
  testCategory: TestCategory;   // 测试分类
  tags: string[];              // 标签
  
  // 执行配置
  executionConfig: ExecutionConfig;
  
  // 生成信息
  generatedBy: string;          // 生成模型
  generationPrompt: string;     // 生成 Prompt
  sourceRequirement: string;    // 来源需求
  
  // 状态管理
  status: TestStatus;           // 用例状态
  version: number;             // 版本号
  
  // 时间戳
  createdAt: Date;
  updatedAt: Date;
}

type TestType = 'BUILD' | 'STATIC' | 'DYNAMIC' | 'SEMANTIC';

type TestCategory = 
  | 'CRUD'           // 增删改查
  | 'PERMISSION'     // 权限
  | 'WORKFLOW'       // 审批流
  | 'INTEGRATION'    // 集成
  | 'EDGE_CASE'      // 边界
  | 'PERFORMANCE'    // 性能
  | 'REGRESSION';    // 回归

type TestStatus = 'DRAFT' | 'ACTIVE' | 'DEPRECATED' | 'MAINTENANCE';

interface ExecutionConfig {
  timeout: number;              // 超时时间(ms)
  retryCount: number;           // 重试次数
  priority: number;            // 执行优先级(越小越高)
  parallelizable: boolean;     // 是否可并行
  dependencies: string[];      // 依赖的用例ID
  environment: string;         // 执行环境
}
```

### 2.4 测试步骤 (TestStep)

```typescript
interface TestStep {
  id: string;                    // 步骤ID
  testId: string;              // 所属用例ID
  order: number;               // 步骤顺序
  name: string;                // 步骤名称
  
  // 步骤类型和内容
  stepType: StepType;           // 步骤类型
  action: StepAction;           // 执行动作
  target: StepTarget;           // 目标元素/接口
  parameters: Record<string, any>; // 参数
  waitCondition: WaitCondition;// 等待条件
  
  // 预期结果
  expectedResult: ExpectedResult;
  
  // 截图/日志配置
  captureScreenshot: boolean;  // 是否截图
  captureLogs: boolean;        // 是否记录日志
  
  metadata: StepMetadata;       // 扩展元数据
}

type StepType = 'NAVIGATE' | 'INTERACT' | 'VERIFY' | 'WAIT' | 'API' | 'DATA_CHECK';

type StepAction = 
  // 导航
  | 'goto' | 'click' | 'doubleClick' | 'rightClick'
  // 输入
  | 'type' | 'select' | 'check' | 'uncheck'
  // 操作
  | 'submit' | 'upload' | 'download' | 'drag'
  // 等待
  | 'waitForElement' | 'waitForResponse' | 'waitForNavigation'
  // API
  | 'httpGet' | 'httpPost' | 'httpPut' | 'httpDelete'
  // 数据校验
  | 'assertEqual' | 'assertContain' | 'assertMatch' | 'assertCount';

interface StepTarget {
  type: 'selector' | 'xpath' | 'text' | 'role' | 'url' | 'api';
  value: string;
  frame?: string;              // iframe 标识
}

interface WaitCondition {
  type: 'visibility' | 'clickable' | 'hidden' | 'text' | 'response';
  timeout: number;
  value?: string;
}

interface ExpectedResult {
  type: 'element' | 'text' | 'url' | 'api' | 'screenshot' | 'database';
  matchType: 'exact' | 'contain' | 'regex' | 'visual' | 'schema';
  value: any;
  screenshotBaseline?: string; // 截图基准
}

interface StepMetadata {
  createdBy: 'LLM' | 'MANUAL';
  model?: string;
  confidence?: number;
}
```

### 2.5 断言 (Assertion)

```typescript
interface Assertion {
  id: string;                    // 断言ID
  stepId: string;              // 所属步骤ID
  name: string;                // 断言名称
  
  // 断言类型
  assertType: AssertType;
  
  // 断言条件
  actual: AssertTarget;        // 实际值来源
  expected: AssertValue;       // 期望值
  operator: AssertOperator;    // 比较操作符
  
  // 截图比对配置
  visualConfig?: VisualAssertConfig;
  
  // 失败处理
  onFail: AssertFailAction;
}

type AssertType = 
  | 'ELEMENT'        // 元素存在性
  | 'TEXT'          // 文本内容
  | 'VALUE'         // 输入值
  | 'ATTRIBUTE'     // 属性值
  | 'CSS'           // CSS 样式
  | 'VISUAL'        // 视觉比对
  | 'API'           // API 响应
  | 'DATABASE';     // 数据库

type AssertOperator = 'equal' | 'notEqual' | 'contain' | 'notContain' | 'match' | 'greaterThan' | 'lessThan';

type AssertFailAction = 'CONTINUE' | 'STOP' | 'RETRY';

interface AssertTarget {
  source: 'element' | 'api' | 'database' | 'variable';
  selector?: string;
  property?: string;
  jsonPath?: string;
}

interface VisualAssertConfig {
  threshold: number;            // 差异阈值 (0-1)
  ignoreAreas: Rect[];         // 忽略区域
  matchType: 'exact' | 'layout' | 'content';
}
```

### 2.6 测试执行 (TestRun)

```typescript
interface TestRun {
  id: string;                    // 执行ID
  testId: string;              // 执行的用例ID
  runNumber: number;           // 执行轮次
  
  // 执行上下文
  commitId: string;            // Git commit ID
  branch: string;              // 分支
  triggeredBy: string;         // 触发者
  
  // 时间
  startTime: Date;
  endTime?: Date;
  duration?: number;
  
  // 执行结果
  status: RunStatus;
  result?: TestResult;
  
  // 环境信息
  environment: RunEnvironment;
  
  // 重试/修正信息
  retryCount: number;
  corrections: Correction[];
  
  // 产物
  artifacts: Artifact[];
}

type RunStatus = 'PENDING' | 'RUNNING' | 'PASSED' | 'FAILED' | 'TIMEOUT' | 'SKIPPED';

interface RunEnvironment {
  os: string;
  browser?: string;
  viewport?: Viewport;
  baseUrl: string;
  headers?: Record<string, string>;
}

interface Viewport {
  width: number;
  height: number;
  deviceScaleFactor?: number;
}
```

### 2.7 测试结果 (TestResult)

```typescript
interface TestResult {
  id: string;
  runId: string;
  
  // 汇总
  status: 'PASS' | 'FAIL' | 'PARTIAL';
  passCount: number;
  failCount: number;
  skipCount: number;
  
  // 步骤结果
  stepResults: StepResult[];
  
  // 失败信息
  failureInfo?: FailureInfo;
  
  // 截图和日志
  screenshots: Screenshot[];
  logs: LogEntry[];
  
  // 性能数据
  metrics?: ExecutionMetrics;
}

interface StepResult {
  stepId: string;
  status: 'PASS' | 'FAIL' | 'SKIP';
  duration: number;
  startTime: Date;
  endTime: Date;
  
  // 执行详情
  actualAction?: string;
  actualValue?: any;
  error?: string;
  
  // 断言结果
  assertionResults: AssertionResult[];
  
  // 产物
  screenshot?: string;
}

interface AssertionResult {
  assertionId: string;
  status: 'PASS' | 'FAIL';
  actualValue: any;
  expectedValue: any;
  message?: string;
}

interface FailureInfo {
  failedStepId: string;
  failedAssertionId?: string;
  errorType: string;
  errorMessage: string;
  stackTrace?: string;
  screenshot?: string;
}

interface Screenshot {
  stepId: string;
  type: 'before' | 'after' | 'error' | 'baseline' | 'actual';
  url: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

interface LogEntry {
  timestamp: Date;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  message: string;
  source?: string;
}

interface ExecutionMetrics {
  pageLoadTime?: number;
  firstContentfulPaint?: number;
  domContentLoaded?: number;
  resourceLoadTime?: number;
  apiResponseTime?: number;
}
```

### 2.8 修正记录 (Correction)

```typescript
interface Correction {
  id: string;
  runId: string;
  
  // 修正时机
  attemptNumber: number;
  triggeredBy: 'AUTO' | 'MANUAL';
  
  // 失败分析
  failureAnalysis: FailureAnalysis;
  
  // 修正策略
  strategy: CorrectionStrategy;
  
  // 修正内容
  changes: CodeChange[];
  
  // 执行结果
  result: 'SUCCESS' | 'FAILED' | 'PARTIAL';
  newError?: string;
  
  // 时间
  createdAt: Date;
  duration: number;
}

interface FailureAnalysis {
  errorType: string;
  errorMessage: string;
  rootCause?: string;
  relatedCode?: string;
  similarCases?: string[];
}

interface CorrectionStrategy {
  approach: string;
  prompt?: string;
  model?: string;
  reasoning?: string;
}

interface CodeChange {
  file: string;
  changeType: 'ADD' | 'MODIFY' | 'DELETE';
  before?: string;
  after?: string;
  diff?: string;
}
```

### 2.9 失败案例库 (FailureCase)

```typescript
interface FailureCase {
  id: string;
  
  // 分类信息
  testType: TestType;
  errorCategory: string;
  errorPattern: string;
  
  // 失败详情
  originalError: string;
  rootCause: string;
  
  // 修复记录
  fixAttempts: FixAttempt[];
  successRate: number;
  averageFixTime: number;
  
  // 学习价值
  tags: string[];
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  
  // 元数据
  firstSeen: Date;
  lastSeen: Date;
  occurrenceCount: number;
  
  // 建议
  suggestedStrategy?: string;
  preventionTips?: string;
}

interface FixAttempt {
  strategy: string;
  result: 'SUCCESS' | 'FAILED';
  fixCode?: string;
  notes?: string;
}
```

## 三、API 响应结构

### 3.1 用例生成 API

```typescript
// 请求
interface GenerateTestsRequest {
  projectId: string;
  featureId: string;
  requirementText: string;
  testTypes: TestType[];
  options?: {
    count?: number;
    includeEdgeCases?: boolean;
    includeRegression?: boolean;
  };
}

// 响应
interface GenerateTestsResponse {
  tests: AcceptanceTest[];
  generationMetadata: {
    model: string;
    promptTokens: number;
    completionTokens: number;
    duration: number;
  };
}
```

### 3.2 用例执行 API

```typescript
// 请求
interface RunTestRequest {
  testId: string;
  commitId: string;
  environment?: Partial<RunEnvironment>;
  options?: {
    captureScreenshots?: boolean;
    parallelSteps?: boolean;
  };
}

// 响应
interface RunTestResponse {
  runId: string;
  status: RunStatus;
  result?: TestResult;
}
```

## 四、数据库表设计

```sql
-- 项目表
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(32) NOT NULL,
    repo_url TEXT,
    framework VARCHAR(64),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 功能表
CREATE TABLE features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    requirement_doc TEXT,
    priority VARCHAR(8),
    status VARCHAR(32) DEFAULT 'DRAFT',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 验收用例表
CREATE TABLE acceptance_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_id UUID REFERENCES features(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    test_type VARCHAR(32) NOT NULL,
    test_category VARCHAR(32),
    tags TEXT[],
    execution_config JSONB DEFAULT '{}',
    generated_by VARCHAR(64),
    generation_prompt TEXT,
    status VARCHAR(32) DEFAULT 'DRAFT',
    version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 测试步骤表
CREATE TABLE test_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID REFERENCES acceptance_tests(id),
    step_order INT NOT NULL,
    name VARCHAR(255),
    step_type VARCHAR(32) NOT NULL,
    action VARCHAR(64) NOT NULL,
    target JSONB NOT NULL,
    parameters JSONB DEFAULT '{}',
    wait_condition JSONB,
    expected_result JSONB,
    capture_screenshot BOOLEAN DEFAULT false,
    capture_logs BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'
);

-- 测试执行记录表
CREATE TABLE test_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID REFERENCES acceptance_tests(id),
    run_number INT NOT NULL,
    commit_id VARCHAR(64),
    branch VARCHAR(128),
    triggered_by VARCHAR(64),
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,
    status VARCHAR(32) DEFAULT 'PENDING',
    result JSONB,
    environment JSONB,
    retry_count INT DEFAULT 0,
    artifacts JSONB DEFAULT '[]'
);

-- 失败案例表
CREATE TABLE failure_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_type VARCHAR(32),
    error_category VARCHAR(64),
    error_pattern TEXT,
    original_error TEXT,
    root_cause TEXT,
    fix_attempts JSONB DEFAULT '[]',
    success_rate DECIMAL(5,2),
    tags TEXT[],
    severity VARCHAR(16),
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    occurrence_count INT DEFAULT 1
);

-- 索引
CREATE INDEX idx_tests_feature ON acceptance_tests(feature_id);
CREATE INDEX idx_tests_type ON acceptance_tests(test_type);
CREATE INDEX idx_steps_test ON test_steps(test_id);
CREATE INDEX idx_runs_test ON test_runs(test_id);
CREATE INDEX idx_runs_status ON test_runs(status);
CREATE INDEX idx_failures_pattern ON failure_cases(error_pattern);
```

## 五、数据流转示例

### 5.1 用例生成流程

```json
{
  "input": {
    "projectId": "proj-001",
    "featureId": "feat-001",
    "requirementText": "用户管理模块 - 支持新增、编辑、删除用户，管理员可以分配角色"
  },
  "process": [
    "1. LLM 解析需求，提取功能点",
    "2. 根据 testTypes 生成对应用例",
    "3. 每个用例生成具体步骤",
    "4. 为步骤配置断言"
  ],
  "output": {
    "tests": [
      {
        "id": "test-001",
        "name": "新增用户-构建验收",
        "testType": "BUILD",
        "steps": [
          {
            "stepType": "API",
            "action": "httpPost",
            "target": { "type": "api", "value": "/api/users" },
            "expectedResult": { "type": "api", "matchType": "schema" }
          }
        ]
      },
      {
        "id": "test-002",
        "name": "新增用户-动态验收",
        "testType": "DYNAMIC",
        "steps": [
          { "stepType": "NAVIGATE", "action": "goto", "target": { "type": "url", "value": "/users/add" } },
          { "stepType": "INTERACT", "action": "type", "target": { "type": "selector", "value": "#username" } },
          { "stepType": "INTERACT", "action": "submit", "target": { "type": "selector", "value": "button[type=submit]" } },
          { "stepType": "VERIFY", "action": "assertEqual", "expectedResult": { "type": "url", "contain": "/users" } }
        ]
      }
    ]
  }
}
```

### 5.2 执行结果记录

```json
{
  "runId": "run-001",
  "testId": "test-002",
  "status": "FAILED",
  "stepResults": [
    {
      "stepId": "step-001",
      "status": "PASS",
      "duration": 1200
    },
    {
      "stepId": "step-002",
      "status": "PASS",
      "duration": 800
    },
    {
      "stepId": "step-003",
      "status": "FAIL",
      "duration": 500,
      "error": "Element is not interactable",
      "assertionResults": [
        {
          "assertionId": "assert-001",
          "status": "FAIL",
          "expectedValue": "提交成功",
          "actualValue": "元素不可交互"
        }
      ]
    }
  ],
  "failureInfo": {
    "failedStepId": "step-003",
    "errorType": "InteractionFailed",
    "errorMessage": "提交按钮被弹窗遮挡"
  }
}
```

## 六、版本演进

| 版本 | 变更说明 |
|------|----------|
| v1.0 | 初始版本，核心实体和关系 |
| v1.1 | 增加修正记录 (Correction) |
| v1.2 | 增加失败案例库 (FailureCase) |
| v1.3 | 优化视觉比对配置 |
| v1.4 | 增加性能指标 (ExecutionMetrics) |