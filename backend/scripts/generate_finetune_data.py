#!/usr/bin/env python
"""
RAG 微调数据生成脚本
从现有系统和人工标注中生成训练数据集
"""

import json
import os
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.db_models import Document, DocumentChunk
from app.services.rag_service import RAGService
from app.core.llm import llm_client


class FinetuneDataGenerator:
    """微调数据生成器"""

    def __init__(self):
        self.db = SessionLocal()
        self.rag = RAGService(self.db)

    async def generate_training_pair(
        self, question: str, ideal_answer: str, relevant_chunks: List[int]
    ) -> Dict:
        """生成单个训练样本（Alpaca 格式）"""

        # 检索文档
        docs = await self.rag.retrieve_documents(question, top_k=10)

        # 构建上下文（只选择标注的相关块）
        selected_docs = [docs[i] for i in relevant_chunks if i < len(docs)]
        context = "\n\n".join([f"文档 {i+1}: {doc['text']}" for i, doc in enumerate(selected_docs)])

        return {
            "instruction": "请基于提供的文档内容准确回答问题，并标注引用来源。",
            "input": f"文档内容：\n{context}\n\n问题：{question}",
            "output": ideal_answer,
            "metadata": {
                "document_ids": [doc["document_id"] for doc in selected_docs],
                "chunk_indices": [doc["chunk_index"] for doc in selected_docs],
                "timestamp": datetime.now().isoformat(),
            }
        }

    async def auto_generate_from_logs(self) -> List[Dict]:
        """从历史对话日志自动生成（需人工审核）"""
        # TODO: 从 QueryCache 表读取历史问答
        # 标注：哪些回答是高质量的 → 作为正样本
        pass

    def export_to_jsonl(self, data: List[Dict], filename: str):
        """导出为 JSONL 格式（微调通用格式）"""
        filepath = os.path.join("backend/data/finetune", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        print(f"✅ 导出 {len(data)} 条训练数据到 {filepath}")

    def close(self):
        self.db.close()


# 示例：生成电商场景的训练数据
EXAMPLE_QUESTIONS = [
    {
        "question": "公司的退货政策是什么？",
        "ideal_answer": "根据《售后服务管理办法》第3条规定：\n1. 商品购买后7天内可无理由退货\n2. 退货商品需保持原包装完好\n3. 退款将在收到退货后3个工作日内处理\n\n引用来源：《售后服务管理办法》第3条",
        "relevant_chunks": [0, 2],  # 指定相关的文档块索引
    },
    {
        "question": "如何申请报销？",
        "ideal_answer": "报销流程如下：\n1. 登录系统提交报销申请单\n2. 上传发票照片和相关凭证\n3. 部门主管审批（3个工作日内）\n4. 财务审核后转账\n\n注意：单次报销金额超过5000元需总经理审批\n引用来源：《财务管理制度》第5章",
        "relevant_chunks": [1, 3],
    },
]


async def main():
    """生成训练数据示例"""
    generator = FinetuneDataGenerator()

    training_data = []
    for example in EXAMPLE_QUESTIONS:
        pair = await generator.generate_training_pair(
            example["question"],
            example["ideal_answer"],
            example["relevant_chunks"]
        )
        training_data.append(pair)

    # 导出训练集
    generator.export_to_jsonl(training_data, "rag_train_v1.jsonl")

    # 导出验证集（建议 10% 数据）
    generator.export_to_jsonl(training_data[:1], "rag_val_v1.jsonl")

    generator.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())