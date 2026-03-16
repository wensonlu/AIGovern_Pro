from typing import Optional
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from app.core.llm import llm_client
from app.models.schemas import ChatResponse, SourceReference
from app.core.database import SessionLocal
from datetime import datetime


class RAGService:
    """RAG 检索增强生成服务（使用 pgvector）"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session
        self.llm = llm_client

    async def retrieve_documents(self, query: str, top_k: int = 5) -> list[dict]:
        """从 pgvector 检索相关文档"""
        try:
            # 生成查询向量
            query_embedding = await self.llm.generate_embedding(query)

            # 截断到 768 维（与数据库列定义一致）
            query_embedding_768 = query_embedding[:768] if len(query_embedding) > 768 else query_embedding

            # 使用 pgvector 进行余弦相似度搜索
            db = self.db or SessionLocal()

            # SQL 查询：JOIN documents 表来获取文件名
            sql = text("""
                SELECT
                    dc.id,
                    dc.document_id,
                    dc.chunk_index,
                    dc.chunk_text,
                    d.title,
                    d.filename,
                    1 - (dc.embedding <=> CAST(:query_embedding AS vector(768))) as relevance
                FROM document_chunks_with_vectors dc
                JOIN documents d ON dc.document_id = d.id
                WHERE dc.embedding IS NOT NULL
                ORDER BY dc.embedding <=> CAST(:query_embedding AS vector(768))
                LIMIT :top_k
            """)

            # 将向量转换为字符串格式（pgvector 接受 [x,y,z,...] 格式）
            embedding_str = "[" + ",".join(map(str, query_embedding_768)) + "]"

            results = db.execute(
                sql,
                {"query_embedding": embedding_str, "top_k": top_k}
            ).fetchall()

            documents = []
            for row in results:
                # 将相关度限制在 0-1 范围内
                relevance = float(row.relevance) if row.relevance else 0.0
                relevance = max(0.0, min(1.0, relevance))

                documents.append({
                    "document_id": row.document_id,
                    "chunk_id": row.id,
                    "chunk_index": row.chunk_index,
                    "text": row.chunk_text,
                    "title": row.title,
                    "filename": row.filename,
                    "relevance": relevance,
                })

            return documents

        except Exception as e:
            print(f"❌ pgvector 检索失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def generate_answer(
        self, question: str, retrieved_docs: list[dict], top_k: int = 5
    ) -> tuple[str, list[SourceReference], float]:
        """基于检索文档生成回答"""

        # 构建上下文
        context = "\n\n".join(
            [f"文档 {i+1}: {doc['text']}" for i, doc in enumerate(retrieved_docs[:top_k])]
        )

        if retrieved_docs:
            prompt = f"""请基于以下文档回答问题。

文档内容：
{context}

问题：{question}

要求：
1. 基于提供的文档内容回答
2. 标注引用的文档位置
3. 如果文档中没有完全相关的信息，请说明
"""
        else:
            prompt = f"""知识库中没有匹配的内容。请基于您的一般知识回答以下问题：

问题：{question}

要求：
1. 清楚地说明"知识库中没有找到相关文档，以下是基于一般知识的回答"
2. 提供有帮助的回答
3. 如果不确定，请说明
"""

        # 生成回答
        answer = await self.llm.generate_text(prompt, max_tokens=1024)

        # 构建信息源引用
        sources = []
        for i, doc in enumerate(retrieved_docs[:top_k]):
            relevance = doc.get("relevance", 0.0)
            # 计算百分比格式 (85%)
            relevance_pct = round(relevance * 100)

            sources.append(
                SourceReference(
                    document_id=doc.get("document_id"),
                    title=doc.get("title", f"文档 {i+1}"),
                    filename=doc.get("filename"),  # 添加实际文件名
                    chunk_index=doc.get("chunk_index"),
                    relevance=relevance,
                    relevance_percentage=f"{relevance_pct}%",  # 百分比格式
                    text_preview=doc.get("text", "")[:200],
                )
            )

        # 计算置信度（基于文档相关性的平均值）
        if retrieved_docs:
            confidence = sum(doc.get("relevance", 0) for doc in retrieved_docs[:top_k]) / max(
                len(retrieved_docs[:top_k]), 1
            )
        else:
            confidence = 0.0

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
