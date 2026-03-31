## Claude Code MCP Server 配置指南

### 当前配置
- ✅ DeepWiki MCP (`.mcp.json`) - 启用
- ❌ 所有项目MCP服务器 - 已禁用（修复API错误）

### 如果你需要其他MCP服务器

编辑 `.claude/settings.json`，在 `enabledPlugins` 后添加：

```json
{
  "mcpServers": {
    "supabase": {
      "type": "sse",
      "url": "http://localhost:3000/mcp",
      "tools": ["execute_sql", "list_tables"]
    },
    "vercel": {
      "type": "http",
      "url": "https://your-mcp-server.com",
      "tools": ["list_deployments", "get_project"]
    }
  }
}
```

### 启用全局项目MCP服务器（谨慎）

如果未来确实需要所有MCP服务器，可以这样修复：
```json
"enableAllProjectMcpServers": false,
"excludeMcpServers": ["firebase"]
```

目前建议保持为 `false`。
