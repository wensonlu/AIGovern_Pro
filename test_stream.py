#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000"

test_case = {
    "question": "公司有哪些核心产品？",
    "session_id": "test_stream_session",
    "top_k": 5,
}

print("🚀 测试流式API: /api/chat/stream\n")
print(f"问题: {test_case['question']}\n")

try:
    response = requests.post(
        f"{BASE_URL}/api/chat/stream",
        json=test_case,
        stream=True,
        timeout=30,
    )

    if response.status_code == 200:
        print("📡 接收流式响应：\n")
        for line in response.iter_lines():
            if line:
                try:
                    event = json.loads(line)
                    event_type = event.get("type", "unknown")
                    print(f"[{event_type}] {json.dumps(event, ensure_ascii=False, indent=2)}")
                except json.JSONDecodeError:
                    print(f"解析错误: {line}")
    else:
        print(f"❌ 错误状态: {response.status_code}")
        print(f"响应: {response.text[:500]}")

except Exception as e:
    print(f"❌ 请求失败: {e}")
