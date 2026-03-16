#!/usr/bin/env python3
"""LLM 模型测试脚本"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ 已加载 .env 文件\n")
except ImportError:
    print("⚠️  未安装 python-dotenv，跳过 .env 加载\n")

from app.core.config import settings
from app.core.llm import LLMClient


async def test_llm():
    """测试 LLM 模型"""
    print("=" * 60)
    print("🧪 AIGovern Pro LLM 测试")
    print("=" * 60)

    # 1. 显示配置
    print("\n📋 当前配置：")
    print(f"  LLM_PROVIDER: {settings.llm_provider}")
    print(f"  LLM_API_KEY: {'*' * 20 + settings.llm_api_key[-10:] if settings.llm_api_key else '未配置'}")
    print(f"  LLM_MODEL_NAME: {settings.llm_model_name}")
    print(f"  LLM_API_BASE: {settings.llm_api_base}")

    # 2. 检查提供者
    print("\n🔍 检查 LLM 提供者...")
    if settings.llm_provider not in ["doubao", "qwen"]:
        print(f"  ⚠️  警告：不支持的 LLM 提供者: {settings.llm_provider}")
        print(f"  ✅ 支持的提供者: doubao, qwen")
        print(f"  💡 建议：将 .env 中的 LLM_PROVIDER 改为 'doubao' 或 'qwen'")
    else:
        print(f"  ✅ 提供者配置正确: {settings.llm_provider}")

    # 3. 初始化客户端
    print("\n🔌 初始化 LLM 客户端...")
    try:
        llm_client = LLMClient()
        print("  ✅ 客户端初始化成功")
    except Exception as e:
        print(f"  ❌ 初始化失败: {e}")
        return False

    # 4. 测试嵌入向量生成
    print("\n📊 测试嵌入向量生成...")
    test_text = "这是一个测试文本"
    try:
        embedding = await llm_client.generate_embedding(test_text)
        print(f"  ✅ 成功生成 {len(embedding)} 维向量")
        print(f"  向量样本（前5维）: {embedding[:5]}")
        print(f"  向量范围: [{min(embedding):.4f}, {max(embedding):.4f}]")
    except Exception as e:
        print(f"  ❌ 嵌入向量生成失败: {e}")
        return False

    # 5. 测试文本生成
    print("\n💬 测试文本生成...")
    test_prompt = "新员工入职有哪些步骤？"
    try:
        response = await llm_client.generate_text(test_prompt)
        print(f"  ✅ 成功生成文本响应")
        print(f"  提示词: {test_prompt}")
        print(f"  响应长度: {len(response)} 字符")
        print(f"  响应预览:\n{response[:200]}...")
    except Exception as e:
        print(f"  ❌ 文本生成失败: {e}")
        return False

    # 6. 测试多个文本的一致性
    print("\n🔄 测试向量生成的一致性...")
    texts = ["测试文本1", "测试文本2", "测试文本1"]  # 相同的文本应该生成相同的向量
    embeddings = []
    try:
        for text in texts:
            embedding = await llm_client.generate_embedding(text)
            embeddings.append(embedding)

        # 检查相同文本是否生成相同的向量
        if embeddings[0] == embeddings[2]:
            print("  ✅ 相同文本生成相同向量（一致性正确）")
        else:
            print("  ⚠️  相同文本生成不同向量（非确定性）")

        # 检查不同文本是否生成不同的向量
        if embeddings[0] != embeddings[1]:
            print("  ✅ 不同文本生成不同向量")
        else:
            print("  ⚠️  不同文本生成相同向量（异常）")
    except Exception as e:
        print(f"  ❌ 一致性测试失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)

    # 7. 配置建议
    if settings.llm_provider not in ["doubao", "qwen"]:
        print("\n⚠️  配置调整建议：")
        print(f"  1. 编辑 .env 文件")
        print(f"  2. 将 LLM_PROVIDER=volcengine 改为 LLM_PROVIDER=doubao")
        print(f"  3. 保存后重启后端服务")

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_llm())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️  测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
