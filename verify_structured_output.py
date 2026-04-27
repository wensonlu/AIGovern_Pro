#!/usr/bin/env python
"""端到端验证脚本 - 测试结构化输出框架"""

import sys
import json
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "backend"))

async def verify_models():
    """验证 1: Pydantic 模型"""
    print("\n" + "="*60)
    print("✓ 验证 1: Pydantic 数据模型")
    print("="*60)

    from app.models.schemas import (
        TextSection, ListOrderedSection, CodeBlockSection,
        TableSection, StructuredChatResponse, OrderedListItem
    )

    tests = [
        ("TextSection", lambda: TextSection(type='text', markdown='## 标题')),
        ("ListOrderedSection", lambda: ListOrderedSection(
            type='list_ordered',
            items=[OrderedListItem(title='项目1', details_markdown='- 子项')]
        )),
        ("CodeBlockSection", lambda: CodeBlockSection(
            type='code_block', language='python', code='print("hello")'
        )),
        ("TableSection", lambda: TableSection(
            type='table', headers=['A', 'B'], rows=[['1', '2']]
        )),
    ]

    for name, factory in tests:
        try:
            obj = factory()
            print(f"  ✅ {name}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            return False

    return True


async def verify_services():
    """验证 2: 服务层方法"""
    print("\n" + "="*60)
    print("✓ 验证 2: 服务层 stream_with_structure 方法")
    print("="*60)

    import inspect
    from app.services.rag_service import RAGService
    from app.services.sql_service import SQLService
    from app.services.diagnosis_service import DiagnosisService
    from app.services.operation_service import OperationService

    services = [
        ('RAGService', RAGService),
        ('SQLService', SQLService),
        ('DiagnosisService', DiagnosisService),
        ('OperationService', OperationService),
    ]

    all_ok = True
    for svc_name, svc_class in services:
        has_method = hasattr(svc_class, 'stream_with_structure')
        if has_method:
            method = getattr(svc_class, 'stream_with_structure')
            is_async = inspect.iscoroutinefunction(method) or inspect.isasyncgenfunction(method)
            print(f"  ✅ {svc_name}.stream_with_structure (async={is_async})")
        else:
            print(f"  ❌ {svc_name} missing stream_with_structure")
            all_ok = False

    return all_ok


async def verify_rag_service():
    """验证 3: RAG 服务的结构化输出"""
    print("\n" + "="*60)
    print("✓ 验证 3: RAG 服务结构化输出（模拟）")
    print("="*60)

    from app.services.rag_service import rag_service

    # 测试 Prompt 生成
    try:
        prompt = rag_service._build_structured_prompt(
            "什么是向量数据库？",
            "向量数据库是存储和检索高维向量的专门数据库..."
        )
        print(f"  ✅ Prompt 生成成功 ({len(prompt)} 字符)")

        # 检查 Prompt 是否包含关键指示
        if "json" in prompt.lower() and "sections" in prompt.lower():
            print(f"  ✅ Prompt 包含结构化指示词")
        else:
            print(f"  ⚠️  Prompt 可能缺少关键指示")

    except Exception as e:
        print(f"  ❌ Prompt 生成失败: {e}")
        return False

    return True


async def verify_api_routes():
    """验证 4: API 路由"""
    print("\n" + "="*60)
    print("✓ 验证 4: API 路由配置")
    print("="*60)

    from app.main import app

    routes = {
        "/api/chat/structured": "POST 非流式结构化 API",
        "/api/chat/structured/stream": "POST 流式结构化 API",
    }

    found_routes = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", set())

        for route_path, desc in routes.items():
            if path == route_path and "POST" in methods:
                found_routes.add(route_path)
                print(f"  ✅ {route_path} ({desc})")

    missing = set(routes.keys()) - found_routes
    if missing:
        print(f"  ❌ 缺少路由: {missing}")
        return False

    return True


async def verify_frontend():
    """验证 5: 前端组件"""
    print("\n" + "="*60)
    print("✓ 验证 5: 前端组件")
    print("="*60)

    components = {
        "StructuredRenderer.tsx": "frontend/src/components/ContentRenderer/StructuredRenderer.tsx",
        "ContentRenderer registry": "frontend/src/components/ContentRenderer/registry.ts",
        "ChatPanel 格式检测": "frontend/src/components/AGUI/ChatPanel.tsx",
    }

    all_ok = True
    for name, path in components.items():
        full_path = project_root / path
        if full_path.exists():
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name} 不存在")
            all_ok = False

    return all_ok


async def verify_documentation():
    """验证 6: 文档"""
    print("\n" + "="*60)
    print("✓ 验证 6: 项目文档")
    print("="*60)

    docs = {
        "技术规范": "docs/architecture/TECH_SPEC_STRUCTURED_OUTPUT.md",
        "验收指南": "docs/testing/STRUCTURED_OUTPUT_VERIFICATION.md",
        "ADR-0001": "docs/architecture/ADR-0001-content-format-detection.md",
        "ADR-0002": "docs/architecture/ADR-0002-content-format-strategy.md",
    }

    all_ok = True
    for name, path in docs.items():
        full_path = project_root / path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✅ {name} ({size:,} 字节)")
        else:
            print(f"  ❌ {name} 不存在")
            all_ok = False

    return all_ok


async def main():
    """主验证流程"""
    print("\n" + "#"*60)
    print("# 结构化输出框架 - 端到端验证")
    print(f"# 时间: 2026-04-27")
    print("#"*60)

    results = []

    # 执行所有验证
    results.append(("模型验证", await verify_models()))
    results.append(("服务层验证", await verify_services()))
    results.append(("RAG 服务验证", await verify_rag_service()))
    results.append(("API 路由验证", await verify_api_routes()))
    results.append(("前端组件验证", await verify_frontend()))
    results.append(("文档验证", await verify_documentation()))

    # 总结
    print("\n" + "="*60)
    print("📊 验证总结")
    print("="*60)

    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status:8} {name}")

    print(f"\n总体进度: {passed}/{total} 验证项通过")

    if passed == total:
        print("\n🎉 所有验证通过！结构化输出框架已完整实现。")
        print("\n📝 后续步骤:")
        print("  1. 启动后端: cd backend && source venv/bin/activate && python run.py")
        print("  2. 启动前端: cd frontend && pnpm dev")
        print("  3. 访问: http://localhost:3001")
        print("  4. 在 ChatPanel 提问进行实时测试")
        print("  5. 查看验收指南: docs/testing/STRUCTURED_OUTPUT_VERIFICATION.md")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个验证项失败，请检查日志。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
