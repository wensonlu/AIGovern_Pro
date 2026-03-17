#!/bin/bash
# CloudStudio 部署初始化脚本

cd /workspace/backend

# 创建 .env 文件
cat > .env << 'EOF'
# LLM 配置
LLM_PROVIDER=doubao
LLM_API_KEY=fe0561a5-293a-4664-9927-0f04a72380ac
LLM_MODEL_NAME=doubao-1-5-pro-32k-250115
LLM_API_BASE=https://ark.cn-beijing.volces.com/api/v3

# Embedding 配置
EMBEDDING_PROVIDER=qwen
EMBEDDING_MODEL_NAME=text-embedding-v1
EMBEDDING_API_KEY=sk-5950f18012e047518b4a36e82dfb6775
EMBEDDING_API_BASE=https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding

# 数据库
DATABASE_URL=postgresql://postgres.jdfrubpfjwhbvxfdyzah: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@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres

# 其他配置
SECRET_KEY=test-secret-key-change-in-production
DEBUG=false
HOST=0.0.0.0
PORT=8000
EOF

echo "✅ 环境变量配置完成"
