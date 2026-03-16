# 🌐 域名配置指南

> 域名: `ai-govern-pro.vercel.app`

---

## ✅ 已完成配置

### 1. 前端配置

**文件:** `frontend/.env.production`
```env
VITE_API_URL=/api
VITE_APP_TITLE=AIGovern Pro
```

**文件:** `frontend/.env.development`
```env
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=AIGovern Pro (Dev)
```

### 2. 后端 CORS 配置

**文件:** `backend/app/main.py`
```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "https://ai-govern-pro.vercel.app",  # ✅ 你的域名
    "https://*.vercel.app",  # 允许所有 Vercel 子域名
],
```

### 3. Vercel 配置

**文件:** `vercel.json`
```json
{
  "name": "ai-govern-pro",
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/$1" },
    { "source": "/docs", "destination": "/api/docs" }
  ]
}
```

### 4. 环境变量模板

**文件:** `.env.example`
```env
VERCEL_URL=https://ai-govern-pro.vercel.app
```

---

## 🚀 部署步骤

### 步骤 1: Vercel Dashboard 设置

1. 登录 [Vercel](https://vercel.com/)
2. 创建新项目，选择 GitHub 仓库
3. 在项目设置中:
   - **Project Name**: `ai-govern-pro` (这样域名就是 ai-govern-pro.vercel.app)
   - **Framework**: Vite
   - **Root Directory**: `./`

### 步骤 2: 配置环境变量

在 Vercel Dashboard → Settings → Environment Variables 中添加:

| 变量名 | 值 | 说明 |
|-------|-----|------|
| `DATABASE_URL` | `postgresql://...` | Supabase 数据库连接 |
| `DOUBAO_API_KEY` | `your-api-key` | 豆包 API Key |
| `DOUBAO_MODEL` | `doubao-pro-32k` | 豆包模型 |
| `SECRET_KEY` | `random-string` | 应用密钥 |
| `VITE_API_URL` | `/api` | 前端 API 地址 |

### 步骤 3: 部署

```bash
# 安装 Vercel CLI
npm i -g vercel

# 登录
vercel login

# 部署
vercel --prod
```

---

## 🔗 部署后的地址

| 用途 | 地址 |
|------|------|
| 前端应用 | https://ai-govern-pro.vercel.app |
| API 接口 | https://ai-govern-pro.vercel.app/api |
| API 文档 | https://ai-govern-pro.vercel.app/docs |
| 健康检查 | https://ai-govern-pro.vercel.app/health |

---

## 📝 自定义域名（可选）

如果你想使用自己的域名（如 `aigovern.yourcompany.com`）:

1. 在 Vercel Dashboard → Settings → Domains
2. 添加你的域名
3. 按提示配置 DNS 解析
4. 等待 SSL 证书自动签发

---

## ⚠️ 注意事项

1. **CORS 已配置** - 确保生产域名在允许列表中
2. **API 路径** - 使用相对路径 `/api`，自动适配域名
3. **环境变量** - 生产环境使用 Vercel Dashboard 设置的变量
4. **HTTPS** - Vercel 自动提供 HTTPS，无需额外配置

---

**配置完成！** 现在可以部署到 `ai-govern-pro.vercel.app` 了 🎉
