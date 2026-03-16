from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from pgvector.sqlalchemy import Vector


class Document(Base):
    """知识库文档表"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), default="general")
    embedding_status = Column(String(50), default="pending")
    chunk_count = Column(Integer, default=0)
    embedding = Column(Vector(768), nullable=True)  # 文档级别嵌入（可选）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    """文档分块表（带向量）"""

    __tablename__ = "document_chunks_with_vectors"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)  # pgvector 768维
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")


class Order(Base):
    """订单表"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class Product(Base):
    """商品表"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    sku = Column(String(50), unique=True, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    category = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(50), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)


class OperationLog(Base):
    """操作日志表"""

    __tablename__ = "operations_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    operation_type = Column(String(100), nullable=False)
    operation_target = Column(String(100), nullable=False)
    operation_detail = Column(JSON)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class Metric(Base):
    """指标数据表"""

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_date = Column(String(10), nullable=False)
    metric_value = Column(Float, nullable=False)
    dimension_1 = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class QueryCache(Base):
    """查询缓存表"""

    __tablename__ = "query_cache"

    id = Column(Integer, primary_key=True, index=True)
    query_hash = Column(String(100), unique=True, nullable=False)
    result = Column(JSON)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
