#!/usr/bin/env python3
"""数据库连接测试脚本"""

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
from app.core.database import engine, SessionLocal, Base


def test_database():
    """测试数据库连接"""
    print("=" * 60)
    print("🧪 数据库连接测试")
    print("=" * 60)

    # 1. 显示配置
    print("\n📋 当前配置：")
    print(f"  DATABASE_URL: {settings.database_url}")
    print(f"  DB_ECHO: {settings.db_echo}")

    # 2. 测试连接
    print("\n🔌 测试数据库连接...")
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("  ✅ 连接成功")
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        return False

    # 3. 创建表
    print("\n📊 创建数据库表...")
    try:
        Base.metadata.create_all(bind=engine)
        print("  ✅ 表创建成功")
    except Exception as e:
        print(f"  ❌ 表创建失败: {e}")
        return False

    # 4. 测试查询
    print("\n🔍 测试数据库查询...")
    try:
        db = SessionLocal()
        # 查询用户表
        from app.models.db_models import User, Document

        user_count = db.query(User).count()
        doc_count = db.query(Document).count()

        print(f"  ✅ 查询成功")
        print(f"     - 用户表: {user_count} 条")
        print(f"     - 文档表: {doc_count} 条")

        db.close()
    except Exception as e:
        print(f"  ❌ 查询失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ 数据库连接测试完成！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        result = test_database()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️  测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
