from typing import Optional
from pymilvus import Collection
from app.core.llm import llm_client
from app.models.schemas import ChatResponse, SourceReference
from datetime import datetime


class RAGService:
    """RAG 检索增强生成服务"""

    def __init__(self, milvus_collection: Optional[Collection] = None):
        self.collection = milvus_collection
        self.llm = llm_client

    async def retrieve_documents(self, query: str, top_k: int = 5) -> list[dict]:
        """从向量库检索相关文档"""
        if not self.collection:
            # 占位符实现 - 实际应连接 Milvus
            return []

        # 生成查询向量
        query_embedding = await self.llm.generate_embedding(query)

        # 从 Milvus 检索相似文档
        search_results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "L2", "params": {"nprobe": 10}},
            limit=top_k,
        )

        documents = []
        for result in search_results[0]:
            documents.append({
                "document_id": result.id,
                "chunk_index": result.fields.get("chunk_index"),
                "text": result.fields.get("text"),
                "relevance": 1 - result.distance,
            })

        return documents

    async def generate_answer(
        self, question: str, retrieved_docs: list[dict], top_k: int = 5
    ) -> tuple[str, list[SourceReference], float]:
        """基于检索文档生成回答"""

        # 构建上下文
        context = "\n\n".join(
            [f"文档 {i+1}: {doc['text']}" for i, doc in enumerate(retrieved_docs[:top_k])]
        )

        prompt = f"""请基于以下文档回答问题。

文档内容：
{context}

问题：{question}

要求：
1. 仅基于提供的文档内容回答
2. 如果文档中没有相关信息，请说明
3. 标注引用的文档位置
"""

        # 生成回答
        answer = await self.llm.generate_text(prompt, max_tokens=1024)

        # 构建信息源引用
        sources = []
        for i, doc in enumerate(retrieved_docs[:top_k]):
            sources.append(
                SourceReference(
                    document_id=doc["document_id"],
                    title=f"文档 {i+1}",
                    chunk_index=doc["chunk_index"],
                    relevance=doc["relevance"],
                    text_preview=doc["text"][:200],
                )
            )

        # 计算置信度（基于文档相关性的平均值）
        confidence = sum(doc["relevance"] for doc in retrieved_docs[:top_k]) / max(
            top_k, 1
        )

        return answer, sources, confidence

    async def process_query(
        self, question: str, session_id: Optional[str] = None, top_k: int = 5
    ) -> ChatResponse:
        """处理完整的对话查询"""

        # 检索相关文档
        retrieved_docs = await self.retrieve_documents(question, top_k)

        # 生成回答
        answer, sources, confidence = await self.generate_answer(question, retrieved_docs)

        return ChatResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            session_id=session_id or "default",
            timestamp=datetime.now(),
        )


# 全局 RAG 服务实例
rag_service = RAGService()
