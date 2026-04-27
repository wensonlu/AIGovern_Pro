#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = "http://localhost:8000"

test_cases = [
    {
        "name": "知识问答 (Knowledge QA)",
        "question": "公司有哪些核心产品？",
        "expected_intent": "knowledge_qa",
    },
    {
        "name": "数据查询 (Data Query)",
        "question": "查询2024年Q1的销售额",
        "expected_intent": "data_query",
    },
    {
        "name": "智能操作 (Smart Operation)",
        "question": "执行数据导出任务",
        "expected_intent": "smart_operation",
    },
    {
        "name": "业务诊断 (Business Diagnosis)",
        "question": "分析用户留存率下降的原因",
        "expected_intent": "business_diagnosis",
    },
]

print("🚀 开始测试4个意图...\n")

for i, test_case in enumerate(test_cases, 1):
    print(f"{'='*60}")
    print(f"测试 {i}: {test_case['name']}")
    print(f"{'='*60}")
    print(f"问题: {test_case['question']}")

    payload = {
        "question": test_case["question"],
        "session_id": f"test_session_{i}",
        "top_k": 5,
    }

    try:
        # 测试非流式API
        print("\n📡 调用 /api/chat (非流式)...")
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            intent = data.get("intent", "unknown")
            print(f"✅ 状态: {response.status_code}")
            print(f"🎯 识别到的意图: {intent}")
            print(f"📊 响应长度: {len(data.get('content', ''))}")
            if intent == test_case["expected_intent"]:
                print("✔️ 意图匹配！")
            else:
                print(f"⚠️ 意图不匹配（期望: {test_case['expected_intent']}）")
        else:
            print(f"❌ 错误状态: {response.status_code}")
            print(f"响应: {response.text[:200]}")

    except Exception as e:
        print(f"❌ 请求失败: {e}")

    print()
    time.sleep(1)

print("\n" + "="*60)
print("🎉 测试完成！")
print("="*60)
