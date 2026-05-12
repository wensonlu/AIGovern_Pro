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
    filename = Column(String(255), nullable=True)  # 上传的原始文件名
    category = Column(String(50), default="general")
    embedding_status = Column(String(50), default="pending")
    chunk_count = Column(Integer, default=0)
    embedding = Column(Vector(768), nullable=True)  # 文档级别嵌入（可选）- Qwen向量截断到768维
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
    embedding = Column(Vector(768), nullable=True)  # pgvector 768维 (Qwen向量截断)
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


class ProductPriceHistory(Base):
    """商品价格修改历史表"""

    __tablename__ = "product_price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    changed_by = Column(String(100), nullable=False)  # 'user' 或 'ai'
    changed_by_id = Column(Integer, nullable=True)  # 用户ID或AI会话ID
    reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")


class AssistantSession(Base):
    """AI 助手会话表"""

    __tablename__ = "assistant_sessions"

    id = Column(String(64), primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AssistantMessage(Base):
    """AI 助手消息表"""

    __tablename__ = "assistant_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AssistantToolCall(Base):
    """AI 助手工具调用记录"""

    __tablename__ = "assistant_tool_calls"

    id = Column(String(64), primary_key=True, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    input_json = Column(JSON, nullable=False)
    output_json = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False, index=True)
    latency_ms = Column(Integer, nullable=True)
    error_code = Column(String(64), nullable=True)
    error_message = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AssistantApproval(Base):
    """AI 助手审批记录"""

    __tablename__ = "assistant_approvals"

    id = Column(String(64), primary_key=True, index=True)
    tool_call_id = Column(String(64), nullable=False, index=True)
    risk_level = Column(String(20), nullable=False)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    status = Column(String(32), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AssistantAuditEvent(Base):
    """AI 助手审计事件"""

    __tablename__ = "assistant_audit_events"

    id = Column(String(64), primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    payload_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
