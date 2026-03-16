from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# 数据库连接
if settings.database_url.startswith("sqlite"):
    # SQLite 配置
    engine = create_engine(
        settings.database_url,
        echo=settings.db_echo,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL 等其他数据库配置（包括 Supabase）
    engine = create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    """获取数据库连接"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

