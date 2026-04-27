#!/usr/bin/env python
"""启动后端服务"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(__file__))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.models import db_models  # 导入所有 ORM 模型
from app.models.db_models import User, Product, Order, Metric

import uvicorn


def seed_data():
    """插入示例数据"""
    session = SessionLocal()
    try:
        # 检查是否已有数据
        if session.query(User).count() > 0:
            return

        # 插入示例用户
        users = [
            User(name="张三", email="zhangsan@example.com", role="admin"),
            User(name="李四", email="lisi@example.com", role="manager"),
            User(name="王五", email="wangwu@example.com", role="user"),
        ]
        session.add_all(users)
        session.commit()

        # 插入示例商品
        products = [
            Product(name="笔记本电脑", sku="LAPTOP001", price=5999.0, stock=50),
            Product(name="鼠标", sku="MOUSE001", price=99.0, stock=200),
            Product(name="键盘", sku="KEYBOARD001", price=199.0, stock=150),
            Product(name="显示器", sku="MONITOR001", price=1999.0, stock=30),
        ]
        session.add_all(products)
        session.commit()

        # 插入示例订单
        orders = [
            Order(user_id=1, product_id=1, quantity=2, amount=11998.0, status="completed"),
            Order(user_id=2, product_id=2, quantity=5, amount=495.0, status="completed"),
            Order(user_id=3, product_id=3, quantity=1, amount=199.0, status="pending"),
            Order(user_id=1, product_id=4, quantity=1, amount=1999.0, status="approved"),
        ]
        session.add_all(orders)
        session.commit()

        # 插入示例指标
        metrics = [
            Metric(metric_name="订单总数", metric_date="2024-03-13", metric_value=1250),
            Metric(metric_name="GMV", metric_date="2024-03-13", metric_value=125000),
            Metric(metric_name="转化率", metric_date="2024-03-13", metric_value=3.5),
            Metric(metric_name="活跃用户", metric_date="2024-03-13", metric_value=5000),
        ]
        session.add_all(metrics)
        session.commit()
    finally:
        session.close()


def main():
    """启动应用"""

    # 初始化数据库表
    print("初始化数据库...")
    Base.metadata.create_all(bind=engine)

    # 插入示例数据
    print("加载示例数据...")
    seed_data()

    # 启动 Uvicorn 服务器
    print(f"启动后端服务于 {settings.host}:{settings.port}")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )


if __name__ == "__main__":
    main()
