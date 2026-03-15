#!/usr/bin/env python3
"""
API 集成验证脚本
测试前后端通信是否正常，验证ChatPanel能否正确调用后端API
"""

import asyncio
import httpx
import json
from typing import Any

API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 30

async def test_health_check() -> dict[str, Any]:
    """测试健康检查"""
    print("\n[测试 1] 健康检查")
    print(f"GET {API_BASE_URL}/health")

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        response = await client.get(f"{API_BASE_URL}/health")
        result = response.json()
        print(f"✓ 状态码: {response.status_code}")
        print(f"✓ 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result

async def test_chat_api() -> dict[str, Any]:
    """测试知识问答 API"""
    print("\n[测试 2] 知识问答 API - /api/chat")

    payload = {
        "question": "新员工入职有哪些步骤？",
        "session_id": "test_session_001",
        "top_k": 5
    }

    print(f"POST {API_BASE_URL}/api/chat")
    print(f"请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        response = await client.post(
            f"{API_BASE_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            print(f"✗ 错误: {response.status_code}")
            print(f"✗ 响应: {response.text}")
            return {}

        result = response.json()
        print(f"✓ 状态码: {response.status_code}")
        print(f"✓ 响应结构:")
        print(f"  - answer: {result.get('answer', '')[:100]}...")
        print(f"  - sources: {len(result.get('sources', []))} 个来源")
        print(f"  - confidence: {result.get('confidence', 0):.2f}")
        print(f"  - session_id: {result.get('session_id')}")
        print(f"  - timestamp: {result.get('timestamp')}")

        # 验证响应格式
        assert "answer" in result, "响应缺少 answer 字段"
        assert "sources" in result, "响应缺少 sources 字段"
        assert "confidence" in result, "响应缺少 confidence 字段"
        assert isinstance(result["sources"], list), "sources 应该是列表"
        assert isinstance(result["confidence"], (int, float)), "confidence 应该是数字"

        print(f"✓ 响应格式验证通过")
        return result

async def test_multiple_queries() -> None:
    """测试多个查询"""
    print("\n[测试 3] 多个查询测试")

    queries = [
        "产品的保修期是多久？",
        "过去7天的订单总数是多少？",
        "这是一个测试问题"
    ]

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        for i, question in enumerate(queries, 1):
            print(f"\n  查询 {i}: {question}")

            try:
                response = await client.post(
                    f"{API_BASE_URL}/api/chat",
                    json={
                        "question": question,
                        "session_id": f"test_session_{i}",
                        "top_k": 5
                    },
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    answer_preview = result.get("answer", "")[:80]
                    print(f"  ✓ 成功 - 回答: {answer_preview}...")
                else:
                    print(f"  ✗ 失败 - 状态码: {response.status_code}")
            except Exception as e:
                print(f"  ✗ 异常: {e}")

async def main():
    """主测试函数"""
    print("=" * 60)
    print("AIGovern Pro - 前后端 API 集成验证")
    print("=" * 60)
    print(f"\n目标服务器: {API_BASE_URL}")

    try:
        # 测试健康检查
        await test_health_check()

        # 测试知识问答 API
        await test_chat_api()

        # 测试多个查询
        await test_multiple_queries()

        print("\n" + "=" * 60)
        print("✓ 所有测试完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        print("\n请确保后端服务正在运行:")
        print(f"  cd backend && python run.py")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
