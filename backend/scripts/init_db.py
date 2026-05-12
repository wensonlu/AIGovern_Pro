#!/usr/bin/env python
"""数据库初始化脚本"""

import sys
import os
from datetime import datetime, timedelta

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
    ProductPriceHistory,
    AssistantSession,
    AssistantMessage,
    AssistantToolCall,
    AssistantApproval,
    AssistantAuditEvent,
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
        session.query(AssistantAuditEvent).delete()
        session.query(AssistantApproval).delete()
        session.query(AssistantToolCall).delete()
        session.query(AssistantMessage).delete()
        session.query(AssistantSession).delete()
        session.query(OperationLog).delete()
        session.query(Order).delete()
        session.query(ProductPriceHistory).delete()
        session.query(Product).delete()
        session.query(User).delete()
        session.query(DocumentChunk).delete()
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

        # 插入示例订单（近30天，包含后两周下滑趋势，便于演示）
        today = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
        orders = []
        daily_amounts = [
            16800, 17200, 17450, 17600, 17800, 18100, 18300, 18500,  # 前期高位
            18200, 18000, 17800, 17600, 17400, 17100, 16900, 16600,  # 震荡回落
            16200, 15800, 15400, 15000, 14700, 14300, 13900, 13500,  # 连续下滑第1周
            13100, 12800, 12400, 12100, 11800, 11500,                # 连续下滑第2周
        ]
        status_cycle = ["completed", "completed", "approved", "pending"]

        for i, total_amount in enumerate(daily_amounts):
            day = today - timedelta(days=(29 - i))
            orders.append(
                Order(
                    user_id=(i % 3) + 1,
                    product_id=((i % 4) + 1),
                    quantity=1 + (i % 3),
                    amount=float(total_amount),
                    status=status_cycle[i % len(status_cycle)],
                    created_at=day,
                )
            )
        session.add_all(orders)
        session.commit()
        print("✅ 插入示例订单")

        # 插入示例指标（带区域维度，便于“华东区”演示）
        metric_day = today.strftime("%Y-%m-%d")
        metrics = [
            Metric(metric_name="订单总数", metric_date=metric_day, metric_value=1480, dimension_1="全国"),
            Metric(metric_name="GMV", metric_date=metric_day, metric_value=526800, dimension_1="全国"),
            Metric(metric_name="转化率", metric_date=metric_day, metric_value=3.2, dimension_1="全国"),
            Metric(metric_name="活跃用户", metric_date=metric_day, metric_value=6820, dimension_1="全国"),
            Metric(metric_name="GMV", metric_date=metric_day, metric_value=182500, dimension_1="华东"),
            Metric(metric_name="订单总数", metric_date=metric_day, metric_value=510, dimension_1="华东"),
            Metric(metric_name="GMV", metric_date=metric_day, metric_value=143200, dimension_1="华南"),
            Metric(metric_name="订单总数", metric_date=metric_day, metric_value=420, dimension_1="华南"),
            Metric(metric_name="GMV", metric_date=metric_day, metric_value=108600, dimension_1="华北"),
            Metric(metric_name="订单总数", metric_date=metric_day, metric_value=350, dimension_1="华北"),
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
