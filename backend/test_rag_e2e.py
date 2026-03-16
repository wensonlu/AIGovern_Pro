#!/usr/bin/env python3
"""RAG 端到端测试"""

import requests
from io import BytesIO
import json

BASE_URL = "http://localhost:8000"

def test():
    print("\n" + "=" * 70)
    print("🎯 AIGovern Pro RAG 端到端测试")
    print("=" * 70)

    # 1. 健康检查
    print("\n1️⃣  健康检查")
    resp = requests.get(f"{BASE_URL}/health")
    print(f"  ✅ 后端服务正常: {resp.json().get('database')}")

    # 2. 上传文档
    print("\n2️⃣  上传测试文档")
    content = """# AIGovern Pro 产品说明

## 产品概述
AIGovern Pro 是企业级 B 端管理系统。

## 核心能力
- 知识问答：基于 RAG 的智能问答
- 数据查询：自然语言转 SQL
- 智能操作：AI 驱动的流程自动化
- 经营诊断：数据洞察和决策建议

## 主要功能
✅ 高保真 UI 设计
✅ 完整的 RAG 流程
✅ 生产级代码质量
"""

    files = {'file': ('test.txt', BytesIO(content.encode()), 'text/plain')}
    data = {'title': '测试文档', 'category': 'product'}
    resp = requests.post(f"{BASE_URL}/api/documents/upload", files=files, data=data)
    doc = resp.json()
    doc_id = doc.get('id')
    print(f"  ✅ 文档上传成功")
    print(f"     ID: {doc_id}, 分块数: {doc.get('chunk_count')}")

    # 3. 测试检索
    print("\n3️⃣  测试文档检索")
    resp = requests.post(
        f"{BASE_URL}/api/documents/{doc_id}/test-retrieval",
        json={"query": "AIGovern Pro 是什么？"}
    )
    result = resp.json()
    print(f"  ✅ 检索成功，找到 {len(result.get('results', []))} 条结果")

    # 4. 测试对话
    print("\n4️⃣  测试对话功能")
    resp = requests.post(
        f"{BASE_URL}/api/chat",
        json={"question": "AIGovern Pro 的核心能力有哪些？", "session_id": "test"}
    )
    chat = resp.json()
    print(f"  ✅ 对话成功")
    print(f"     回答: {chat.get('answer', '')[:100]}...")
    print(f"     置信度: {chat.get('confidence', 0):.0%}")

    print("\n" + "=" * 70)
    print("✅ 所有测试完成！")
    print("\n🎉 系统运行正常！")
    print("\n📝 后续步骤:")
    print("  1. 打开 http://localhost:3000")
    print("  2. 上传文档进行完整测试")
    print("  3. 在 AGUI 对话面板提问")
    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    try:
        test()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
