#!/usr/bin/env python3
"""
Milvus 向量库初始化脚本
创建 documents_embeddings collection
"""

from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
)
from app.core.config import settings

# 连接 Milvus
connections.connect(
    alias="default",
    host=settings.milvus_host,
    port=settings.milvus_port,
)

# 定义字段
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="document_id", dtype=DataType.INT64),
    FieldSchema(name="chunk_index", dtype=DataType.INT32),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.milvus_embedding_dim),
]

# 创建 Collection Schema
schema = CollectionSchema(
    fields=fields,
    description="文档向量集合",
    enable_dynamic_field=True,
)

# 创建或获取 Collection
try:
    collection = Collection(name=settings.milvus_collection, schema=schema)
    print(f"✅ Collection '{settings.milvus_collection}' 已存在")
except Exception:
    collection = Collection(name=settings.milvus_collection, schema=schema)
    print(f"✅ Collection '{settings.milvus_collection}' 创建成功")

# 创建索引（用于加速搜索）
try:
    index_params = {
        "index_type": "IvfFlat",
        "metric_type": "L2",
        "params": {"nlist": 128},
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    print("✅ 索引创建成功")
except Exception as e:
    print(f"⚠️ 索引创建失败: {e}")

# 加载 Collection 到内存
collection.load()
print("✅ Collection 加载到内存成功")
