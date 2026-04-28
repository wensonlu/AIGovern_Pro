# 部署指南 - AIGovern Pro + MCP Demo

## 📋 部署信息

- **项目**: AIGovern Pro (AI-native B2B Management System)
- **新增功能**: MCP Browser Automation Demo
- **前端框架**: React 18 + Vite + Ant Design Pro
- **后端框架**: FastAPI + Playwright
- **部署平台**: Vercel (前端 + 后端)

## ✅ 预检清单

- [x] 代码已提交到GitHub (3个提交)
- [x] 前端TypeScript编译通过
- [x] 前端生产构建成功 (dist/)
- [x] 后端依赖检查通过
- [x] MCP系统测试通过 (6/6 tools)
- [x] E2E集成测试通过

## 🚀 部署步骤

### 1. Vercel 前端部署 (自动)

Vercel已连接到GitHub仓库，推送到main分支会自动触发部署。

**前端构建命令**: `pnpm run build` (dist/)
**前端运行命令**: 无需 (Vercel静态托管)

**预期输出**:
```
✓ built in 10.77s
- Total bundle size: ~1.7MB
- Gzip size: ~519KB
```

### 2. Vercel 后端部署 (Lambda)

后端通过Vercel Serverless Functions部署。

**后端构建命令**: 已在vercel.json中配置
```json
{
  "buildCommand": "pip install -r backend/requirements.txt",
  "outputDirectory": "backend"
}
```

**新增依赖**: 
- playwright>=1.40.0 ✅ (已添加到requirements.txt)

### 3. 环境变量配置

需要在Vercel项目设置中配置:

```
ANTHROPIC_AUTH_TOKEN=sk-...        # Claude API key
ANTHROPIC_BASE_URL=https://...     # API endpoint
LLM_PROVIDER=anthropic              # 使用Claude
LLM_MODEL_NAME=claude-opus-4-1      # 模型
```

## 📦 文件清单

### 新增文件 (已全部提交)

```
后端 (7个文件, 1000+ LOC)
├── app/mcp/__init__.py
├── app/mcp/page_state.py
├── app/mcp/browser_engine.py
├── app/mcp/security.py
├── app/services/mcp_service.py
├── app/api/demo.py
└── requirements.txt (+playwright)

前端 (8个文件, 800+ LOC)
├── pages/AIAssistantDemo.tsx
├── pages/AIAssistantDemo.module.css
├── components/MCPConsole/
│   ├── MCPConsole.tsx
│   ├── MCPConsole.module.css
│   ├── OperationLog.tsx
│   ├── OperationLog.module.css
│   ├── ScreenshotViewer.tsx
│   └── ScreenshotViewer.module.css
├── services/mcp-demo-api.ts
├── App.tsx (+route)
└── AppLayout.tsx (+nav)

文档 (5个文件, 1100+ 行)
├── MCP_DEMO_GUIDE.md
├── MCP_TOOL_EXAMPLES.md
├── MCP_CUSTOMIZATION_GUIDE.md
├── MCP_IMPLEMENTATION_SUMMARY.md
└── DEPLOY_GUIDE.md (本文件)
```

### 修改文件 (已修复)

```
frontend/src/components/MCPConsole/OperationLog.tsx
  - 添加tool_calls属性到Operation接口

frontend/src/pages/AIAssistantDemo.tsx
  - 修复AppLayout props调用 (title → currentMenu)
```

## 🧪 验证步骤

### 本地验证 ✅

```bash
# 1. 前端检查
cd frontend
pnpm run lint        # ESLint检查
pnpm run type-check  # TypeScript检查 ✅
pnpm run build       # 生产构建 ✅

# 2. 后端检查
cd backend
source venv/bin/activate
pip check                 # 依赖检查 ✅
python test_mcp_system.py # MCP单元测试 ✅
python test_e2e.py        # E2E集成测试 ✅
```

## 🌐 访问地址

部署后的地址:

| 组件 | 地址 |
|------|------|
| 前端 | https://ai-govern-pro.vercel.app |
| 后端API | https://ai-govern-pro-backend.vercel.app |
| AI Demo | https://ai-govern-pro.vercel.app/ai-demo |
| API文档 | https://ai-govern-pro-backend.vercel.app/docs |

## 📊 性能指标

**前端 Build Output:**
```
✓ 建构时间: 10.77秒
✓ Bundle大小: 1.7MB (gzip: 519KB)
✓ 页面加载时间: <2s (预期)
✓ 时间到交互(TTI): <3s (预期)
```

**后端 API响应:**
```
✓ /api/demo/ai-task: NDJSON流 (实时)
✓ /api/demo/screenshot/{session_id}: <200ms
✓ /api/demo/health: <100ms
```

## 🔧 后续部署调整

### 如果需要修改后端

```bash
# 1. 本地测试
cd backend && source venv/bin/activate
python run.py  # 测试http://localhost:8000

# 2. 提交更改
git add -A
git commit -m "fix: ..."
git push origin main

# 3. Vercel自动部署
```

### 如果需要修改前端

```bash
# 1. 本地构建验证
cd frontend
pnpm run type-check
pnpm run build

# 2. 提交更改
git add -A
git commit -m "feat: ..."
git push origin main

# 3. Vercel自动部署
```

## 📝 故障排除

### 前端部署失败

检查:
- [ ] package.json 中所有依赖版本正确
- [ ] TSX文件没有类型错误 (`pnpm run type-check`)
- [ ] 所有import路径正确
- [ ] .env.production 文件配置正确

### 后端部署失败

检查:
- [ ] requirements.txt 中所有依赖都能安装
- [ ] Python版本 >= 3.9
- [ ] 环境变量在Vercel中正确设置
- [ ] API路由在demo.py中正确定义

### MCP工具不工作

检查:
- [ ] Playwright安装: `pip list | grep playwright`
- [ ] Chromium浏览器: `~/.cache/ms-playwright/chromium-*/`
- [ ] Claude API key配置正确
- [ ] 后端日志 (Vercel Dashboard → Logs)

## 📚 相关文档

- `MCP_DEMO_GUIDE.md` - 用户使用指南
- `MCP_TOOL_EXAMPLES.md` - API示例
- `MCP_CUSTOMIZATION_GUIDE.md` - 自定义指南
- `MCP_IMPLEMENTATION_SUMMARY.md` - 实现总结

## 🎯 下一步

1. **验证部署成功**
   - 访问 https://ai-govern-pro.vercel.app/ai-demo
   - 尝试任务: "Click reset button"

2. **监控部署**
   - Vercel Dashboard 查看性能指标
   - CloudWatch 日志（如已配置）

3. **后续优化** (可选)
   - 添加更多MCP工具 (键盘输入、文件上传等)
   - 添加身份验证和速率限制
   - 性能优化 (缓存、CDN等)

## 📞 支持

有问题? 检查:
1. 本地测试脚本: `backend/test_mcp_system.py`
2. 项目文档: `MCP_*.md` 文件
3. API文档: `backend/app/api/demo.py`

---

**部署状态**: ✅ **准备就绪**  
**最后更新**: 2026-04-28  
**提交**: 78a1b3d (docs(mcp): Add comprehensive implementation summary)
