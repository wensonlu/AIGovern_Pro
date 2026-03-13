#!/usr/bin/env python
"""数据库初始化脚本"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine, Base
from app.models.db_models import (
    Document,
    DocumentChunk,
    Order,
    Product,
    User,
    OperationLog,
    Metric,
    QueryCache,
)


def init_db():
    """创建所有数据库表"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库初始化完成")


def seed_data():
    """插入示例数据"""
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # 清空现有数据
        session.query(Metric).delete()
        session.query(OperationLog).delete()
        session.query(Order).delete()
        session.query(Product).delete()
        session.query(User).delete()
        session.query(Document).delete()
        session.commit()

        # 插入示例用户
        users = [
            User(name="张三", email="zhangsan@example.com", role="admin"),
            User(name="李四", email="lisi@example.com", role="manager"),
            User(name="王五", email="wangwu@example.com", role="user"),
        ]
        session.add_all(users)
        session.commit()
        print("✅ 插入示例用户")

        # 插入示例商品
        products = [
            Product(name="笔记本电脑", sku="LAPTOP001", price=5999.0, stock=50),
            Product(name="鼠标", sku="MOUSE001", price=99.0, stock=200),
            Product(name="键盘", sku="KEYBOARD001", price=199.0, stock=150),
            Product(name="显示器", sku="MONITOR001", price=1999.0, stock=30),
        ]
        session.add_all(products)
        session.commit()
        print("✅ 插入示例商品")

        # 插入示例订单
        orders = [
            Order(user_id=1, product_id=1, quantity=2, amount=11998.0, status="completed"),
            Order(user_id=2, product_id=2, quantity=5, amount=495.0, status="completed"),
            Order(user_id=3, product_id=3, quantity=1, amount=199.0, status="pending"),
            Order(user_id=1, product_id=4, quantity=1, amount=1999.0, status="approved"),
        ]
        session.add_all(orders)
        session.commit()
        print("✅ 插入示例订单")

        # 插入示例指标
        metrics = [
            Metric(metric_name="订单总数", metric_date="2024-03-13", metric_value=1250),
            Metric(metric_name="GMV", metric_date="2024-03-13", metric_value=125000),
            Metric(metric_name="转化率", metric_date="2024-03-13", metric_value=3.5),
            Metric(metric_name="活跃用户", metric_date="2024-03-13", metric_value=5000),
        ]
        session.add_all(metrics)
        session.commit()
        print("✅ 插入示例指标")

        print("\n✨ 示例数据插入完成")

    except Exception as e:
        print(f"❌ 数据插入失败: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
    seed_data()
