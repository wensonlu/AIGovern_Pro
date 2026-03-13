#!/usr/bin/env python
"""启动后端服务"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from app.core.database import Base, engine
from app.models import db_models  # 导入所有 ORM 模型

import uvicorn


def main():
    """启动应用"""

    # 初始化数据库表
    print("初始化数据库...")
    Base.metadata.create_all(bind=engine)

    # 启动 Uvicorn 服务器
    print(f"启动后端服务于 {settings.host}:{settings.port}")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
