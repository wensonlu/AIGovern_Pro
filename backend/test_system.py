#!/usr/bin/env python3
"""完整系统测试报告"""

import os
import sys
from pathlib import Path

# 添加项目目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.core.config import settings


def test_system():
    """完整系统测试报告"""
    print("=" * 70)
    print("📊 AIGovern Pro 系统测试报告")
    print("=" * 70)

    # 1. LLM 配置
    print("\n✅ LLM 模型配置：")
    print(f"   提供者: {settings.llm_provider}")
    print(f"   API Key: {'已配置 ✅' if settings.llm_api_key else '未配置 ❌'}")
    print(f"   模型: {settings.llm_model_name}")
    print(f"   API Base: {settings.llm_api_base}")

    # 2. 数据库配置
    print("\n📦 数据库配置：")
    print(f"   数据库类型: {'PostgreSQL/Supabase' if 'postgresql' in settings.database_url else 'SQLite (本地演示)' if 'sqlite' in settings.database_url else 'Unknown'}")
    print(f"   数据库 URL: {settings.database_url}")
    print(f"   SQL Echo: {settings.db_echo}")

    # 3. 向量库配置
    print("\n🔍 向量库配置：")
    print(f"   维度: {settings.vector_dimensions}")
    print(f"   相似度指标: {settings.vector_similarity_metric}")

    # 4. 问题诊断
    print("\n⚠️  当前配置状态：")

    issues = []

    # 检查 LLM API Key
    if not settings.llm_api_key:
        issues.append({
            'level': 'warning',
            'title': 'LLM API Key 未配置',
            'desc': '系统会使用 Mock 回复进行演示',
            'action': '如需真实 LLM 能力，设置 LLM_API_KEY'
        })

    # 检查数据库类型
    if 'sqlite' in settings.database_url:
        issues.append({
            'level': 'error',
            'title': '数据库使用 SQLite',
            'desc': 'SQLite 不支持 pgvector 扩展，无法存储向量',
            'action': '切换到 PostgreSQL 或 Supabase'
        })
    elif 'postgresql' in settings.database_url:
        issues.append({
            'level': 'success',
            'title': '数据库配置正确',
            'desc': '使用 PostgreSQL，支持 pgvector 向量存储',
            'action': '需要确保 pgvector 扩展已安装'
        })

    # 显示诊断结果
    for issue in issues:
        if issue['level'] == 'error':
            print(f"\n   ❌ {issue['title']}")
        elif issue['level'] == 'warning':
            print(f"\n   ⚠️  {issue['title']}")
        else:
            print(f"\n   ✅ {issue['title']}")

        print(f"      说明: {issue['desc']}")
        print(f"      建议: {issue['action']}")

    # 5. 建议的后续步骤
    print("\n" + "=" * 70)
    print("📋 建议的后续步骤：")
    print("=" * 70)

    if 'sqlite' in settings.database_url:
        print("""
1️⃣  配置 Supabase PostgreSQL（推荐）
   a. 访问 https://supabase.com → Start project
   b. 创建项目: aigovern-pro
   c. 在控制台执行: CREATE EXTENSION IF NOT EXISTS vector;
   d. 获取连接字符串
   e. 更新 .env:
      DATABASE_URL=postgresql://postgres.YOUR_PROJECT:PASSWORD@aws-0-YOUR_REGION.pooler.supabase.com:5432/postgres

2️⃣  或本地部署 PostgreSQL
   a. 使用 Docker: docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:latest
   b. 安装 pgvector
   c. 更新 .env

3️⃣  测试 LLM 连接
   python3 test_llm.py

4️⃣  启动后端服务
   python3 run.py

5️⃣  前后端集成测试
   a. 启动前端: npm run dev
   b. 上传文档进行测试
   c. 进行知识问答
""")
    else:
        print("""
1️⃣  验证 pgvector 扩展
   在 Supabase SQL Editor 执行:
   SELECT extname FROM pg_extension WHERE extname = 'vector';

2️⃣  测试数据库连接
   python3 test_database.py

3️⃣  初始化数据库
   python3 run.py

4️⃣  测试 LLM 连接
   python3 test_llm.py

5️⃣  启动后端服务
   python3 run.py
""")

    print("=" * 70)


if __name__ == "__main__":
    try:
        test_system()
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
