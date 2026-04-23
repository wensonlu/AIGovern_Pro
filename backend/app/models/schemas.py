from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ==================== 知识库相关 ====================

class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    title: str = Field(..., min_length=1, max_length=200)
    category: str = Field(default="general", max_length=50)


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    title: str
    category: str
    embedding_status: str
    chunk_count: int
    created_at: datetime


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    total: int
    items: list[DocumentResponse]


# ==================== 对话相关 ====================

class ChatRequest(BaseModel):
    """对话请求"""
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class SourceReference(BaseModel):
    """信息源引用"""
    document_id: int
    title: str
    filename: Optional[str] = None  # 上传的原始文件名
    chunk_index: int
    relevance: float = Field(..., ge=0, le=1)  # 0-1 范围，用于计算百分比
    relevance_percentage: str = Field(...)  # "85%" 格式，便于前端直接展示
    text_preview: str


class WorkflowStep(BaseModel):
    """工作流步骤"""
    step: int
    name: str
    status: str  # pending, running, completed, failed
    description: str


class ChatResponse(BaseModel):
    """对话响应"""
    answer: str
    sources: list[SourceReference]
    confidence: float = Field(..., ge=0, le=1)
    session_id: str
    timestamp: datetime
    intent: str = Field(default="knowledge_qa", description="识别到的用户意图")
    workflow: list[WorkflowStep] = Field(default_factory=list, description="处理工作流")


# ==================== 数据查询相关 ====================

class QueryRequest(BaseModel):
    """数据查询请求"""
    natural_language_query: str = Field(..., min_length=1, max_length=2000)
    context: Optional[dict[str, Any]] = None


class QueryResponse(BaseModel):
    """数据查询响应"""
    sql: str
    result: list[dict[str, Any]]
    chart_type: str
    rows_count: int
    execution_time: float


# ==================== 智能操作相关 ====================

class OperationTemplate(BaseModel):
    """操作模板"""
    id: int
    name: str
    description: str
    operation_type: str
    required_params: dict[str, Any]


class OperationExecuteRequest(BaseModel):
    """操作执行请求"""
    operation_type: str
    parameters: dict[str, Any]


class OperationLog(BaseModel):
    """操作日志"""
    id: int
    user_id: int
    operation_type: str
    operation_detail: dict[str, Any]
    status: str
    created_at: datetime


# ==================== 经营诊断相关 ====================

class MetricData(BaseModel):
    """指标数据"""
    name: str
    value: float
    dimension: Optional[str] = None
    date: str


class DiagnosisMetrics(BaseModel):
    """诊断指标"""
    order_metrics: MetricData
    gmv_metrics: MetricData
    conversion_metrics: MetricData
    user_active_metrics: MetricData


class DiagnosisAnalysis(BaseModel):
    """诊断分析"""
    issue: str
    root_cause: str
    recommendation: str
    priority: str  # high, medium, low


# ==================== 商品管理相关 ====================

class ProductResponse(BaseModel):
    """商品响应"""
    id: int
    name: str
    sku: str
    price: float
    stock: int
    category: str
    created_at: datetime


class ProductPriceHistoryResponse(BaseModel):
    """商品价格历史响应"""
    id: int
    product_id: int
    product_name: str
    old_price: float
    new_price: float
    changed_by: str  # 'user' 或 'ai'
    changed_by_id: Optional[int]
    reason: Optional[str]
    created_at: datetime
