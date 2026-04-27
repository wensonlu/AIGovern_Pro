from typing import Any, AsyncIterator, Optional, Union
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from app.core.llm import llm_client, LLMServiceError, LLMTimeoutError
from app.models.schemas import (
    ChatResponse,
    SourceReference,
    StructuredChatResponse,
    TextSection,
    ListOrderedSection,
    ListUnorderedSection,
    OrderedListItem,
    Section,
)
from app.core.database import SessionLocal
from datetime import datetime
import json
import re
import logging

logger = logging.getLogger(__name__)


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

        prompt = self._build_answer_prompt(question, retrieved_docs, top_k)

        # 生成回答。外部 LLM 超时或网络异常不能让 /api/chat 返回 500。
        try:
            answer = await self.llm.generate_text(prompt, max_tokens=1024)
        except LLMTimeoutError:
            if retrieved_docs:
                answer = (
                    "已检索到相关知识库内容，但大模型服务响应超时，暂时无法生成完整回答。"
                    "请稍后重试，或缩短问题范围后再试。"
                )
            else:
                answer = (
                    "知识库中没有找到相关文档，且大模型服务响应超时，暂时无法生成通用回答。"
                    "请稍后重试。"
                )
        except LLMServiceError as e:
            if retrieved_docs:
                answer = (
                    "已检索到相关知识库内容，但大模型服务当前不可用，暂时无法生成完整回答。"
                    f"错误信息：{e}"
                )
            else:
                answer = (
                    "知识库中没有找到相关文档，且大模型服务当前不可用。"
                    f"错误信息：{e}"
                )

        sources = self._build_sources(retrieved_docs, top_k)
        confidence = self._calculate_confidence(retrieved_docs, top_k)

        return answer, sources, confidence

    async def process_query_stream(
        self, question: str, session_id: Optional[str] = None, top_k: int = 5
    ) -> AsyncIterator[dict[str, Any]]:
        """处理完整的流式知识问答查询"""
        retrieved_docs = await self.retrieve_documents(question, top_k)
        sources = self._build_sources(retrieved_docs, top_k)
        confidence = self._calculate_confidence(retrieved_docs, top_k)

        yield {
            "type": "sources",
            "sources": [source.model_dump(mode="json") for source in sources],
            "confidence": confidence,
            "session_id": session_id or "default",
        }

        prompt = self._build_answer_prompt(question, retrieved_docs, top_k)

        try:
            async for chunk in self.llm.stream_text(prompt, max_tokens=1024):
                yield {"type": "delta", "content": chunk}
        except LLMTimeoutError:
            content = (
                "已检索到相关知识库内容，但大模型服务响应超时，暂时无法生成完整回答。"
                "请稍后重试，或缩短问题范围后再试。"
                if retrieved_docs
                else "知识库中没有找到相关文档，且大模型服务响应超时，暂时无法生成通用回答。请稍后重试。"
            )
            yield {"type": "delta", "content": content}
        except LLMServiceError as e:
            content = (
                "已检索到相关知识库内容，但大模型服务当前不可用，暂时无法生成完整回答。"
                f"错误信息：{e}"
                if retrieved_docs
                else f"知识库中没有找到相关文档，且大模型服务当前不可用。错误信息：{e}"
            )
            yield {"type": "delta", "content": content}

        yield {
            "type": "done",
            "confidence": confidence,
            "session_id": session_id or "default",
            "timestamp": datetime.now().isoformat(),
        }

    def _build_answer_prompt(
        self, question: str, retrieved_docs: list[dict], top_k: int
    ) -> str:
        """构建知识问答提示词"""
        context = "\n\n".join(
            [f"文档 {i+1}: {doc['text']}" for i, doc in enumerate(retrieved_docs[:top_k])]
        )

        if retrieved_docs:
            return f"""请基于以下文档回答问题。

文档内容：
{context}

问题：{question}

要求：
1. 基于提供的文档内容回答
2. 标注引用的文档位置
3. 如果文档中没有完全相关的信息，请说明
"""

        return f"""知识库中没有匹配的内容。请基于您的一般知识回答以下问题：

问题：{question}

要求：
1. 清楚地说明"知识库中没有找到相关文档，以下是基于一般知识的回答"
2. 提供有帮助的回答
3. 如果不确定，请说明
"""

    def _build_sources(
        self, retrieved_docs: list[dict], top_k: int
    ) -> list[SourceReference]:
        """构建信息源引用"""
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

        return sources

    def _calculate_confidence(self, retrieved_docs: list[dict], top_k: int) -> float:
        """计算置信度（基于文档相关性的平均值）"""
        if retrieved_docs:
            return sum(doc.get("relevance", 0) for doc in retrieved_docs[:top_k]) / max(
                len(retrieved_docs[:top_k]), 1
            )
        return 0.0

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

    async def stream_with_structure(
        self, question: str, top_k: int = 5
    ) -> AsyncIterator[dict]:
        """
        结构化流式处理 RAG 查询 - 逐块返回 section

        Yields:
            {"type": "sources", "sources": [...], "confidence": 0.85}
            {"type": "section", "section": {"type": "text", "markdown": "..."}}
            {"type": "done", "confidence": 0.85}
        """
        try:
            # 1. 检索相关文档
            retrieved_docs = await self.retrieve_documents(question, top_k)
            sources = self._build_sources(retrieved_docs, top_k)
            confidence = self._calculate_confidence(retrieved_docs, top_k)
            context = self._format_context_for_structured(retrieved_docs)

            # 2. 返回 sources 事件（用户能看到检索到的文档）
            yield {
                "type": "sources",
                "sources": [s.model_dump() for s in sources],
                "confidence": confidence,
            }

            # 3. 构建结构化 prompt（关键：让 LLM 直接输出 JSON）
            prompt = self._build_structured_prompt(question, context)

            # 4. 流式调用 LLM，累积完整响应
            accumulated_content = ""
            try:
                async for chunk in self.llm.stream_text(prompt, max_tokens=2048):
                    accumulated_content += chunk
            except (LLMServiceError, LLMTimeoutError) as e:
                logger.error(f"LLM 流式调用失败: {e}")
                yield {
                    "type": "error",
                    "message": f"LLM 服务错误：{str(e)}"
                }
                return

            # 5. 解析 LLM 输出为 Section 对象
            try:
                sections_data = json.loads(accumulated_content)
                if not isinstance(sections_data, list):
                    sections_data = [sections_data]
            except json.JSONDecodeError:
                logger.warning("LLM 返回的不是有效 JSON，尝试从代码块中提取 JSON")
                extracted_json = self._extract_json_from_codeblock(accumulated_content)
                if extracted_json:
                    try:
                        sections_data = json.loads(extracted_json)
                        if not isinstance(sections_data, list):
                            sections_data = [sections_data]
                    except json.JSONDecodeError:
                        logger.warning("代码块中的 JSON 解析失败，使用降级处理")
                        sections_data = self._parse_markdown_to_sections(accumulated_content)
                else:
                    logger.warning("未找到代码块，使用降级处理")
                    sections_data = self._parse_markdown_to_sections(accumulated_content)

            # 6. 逐块返回 section（用户能实时看到内容生成）
            for section_data in sections_data:
                try:
                    section = self._validate_section(section_data)
                    yield {
                        "type": "section",
                        "section": section.model_dump()
                    }
                except ValueError as e:
                    logger.warning(f"Invalid section data: {e}, skipping")
                    continue

            # 7. 完成事件
            yield {
                "type": "done",
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in stream_with_structure: {e}")
            yield {
                "type": "error",
                "message": f"处理失败：{str(e)}"
            }

    def _build_structured_prompt(self, question: str, context: str) -> str:
        """构建结构化 prompt，让 LLM 输出 JSON"""
        prompt = f"""请基于以下文档回答问题，并按指定的结构化格式返回。

文档内容：
{context}

问题：{question}

==== 重要：返回格式要求 ====
你的回答必须是以下 JSON 格式的数组，每个元素是一个 section：

[
  {{
    "type": "text",
    "markdown": "段落文本，支持 **粗体** 和 [链接](url)"
  }},
  {{
    "type": "list_ordered",
    "items": [
      {{
        "title": "第一项标题",
        "details_markdown": "- 子项1\\n- 子项2"
      }},
      {{
        "title": "第二项标题",
        "details_markdown": "详细信息"
      }}
    ]
  }}
]

要求：
1. 直接返回 JSON 数组，不要有任何其他文字（没有 markdown 代码块标记）
2. 如果内容是有序列表（编号），使用 "list_ordered" 类型
3. 如果内容是无序列表（符号 - 或 •），使用 "list_unordered" 类型
4. markdown 字段支持 **粗体**、[链接]、`代码` 等 markdown 语法
5. 嵌套列表放在 subitems 字段中
6. 确保返回的 JSON 格式正确且可被解析
"""
        return prompt

    def _format_context_for_structured(self, retrieved_docs: list[dict]) -> str:
        """为结构化输出格式化上下文"""
        if not retrieved_docs:
            return "（未检索到相关文档）"

        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(
                f"【文档 {i}】{doc.get('title', '未知')}\n"
                f"相关度: {doc.get('relevance', 0)*100:.0f}%\n"
                f"内容: {doc.get('text', '')[:500]}..."
            )

        return "\n\n".join(context_parts)

    def _validate_section(self, data: dict) -> Section:
        """验证并转换原始数据为 Section 对象"""
        section_type = data.get("type")

        if section_type == "text":
            return TextSection(
                type="text",
                markdown=data.get("markdown", "")
            )

        elif section_type == "list_ordered":
            items = [
                OrderedListItem(
                    title=item.get("title", ""),
                    details_markdown=item.get("details_markdown"),
                    subitems=[
                        OrderedListItem(title=sub.get("title", ""))
                        for sub in item.get("subitems", [])
                    ] if item.get("subitems") else None
                )
                for item in data.get("items", [])
            ]
            return ListOrderedSection(type="list_ordered", items=items)

        elif section_type == "list_unordered":
            items = [
                OrderedListItem(
                    title=item.get("title", ""),
                    details_markdown=item.get("details_markdown")
                )
                for item in data.get("items", [])
            ]
            return ListUnorderedSection(type="list_unordered", items=items)

        else:
            raise ValueError(f"Unknown section type: {section_type}")

    def _extract_json_from_codeblock(self, content: str):
        """从 markdown 代码块中提取 JSON"""
        pattern = r'```(?:json)?\s*\n([\s\S]*?)\n```'
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
        return None

    def _parse_markdown_to_sections(self, content: str) -> list[dict]:
        """
        降级方案：LLM 返回 markdown 时，自动转换为 sections
        这保证了即使 LLM 没完全遵循 JSON 格式，也能降级处理
        """
        sections = []

        # 按 ## 标题分段
        parts = content.split("\n## ")

        for part in parts:
            if not part.strip():
                continue

            # 检测是否为列表
            if part.strip().startswith("-") or re.match(r"^\d+\.", part):
                items = self._extract_list_items(part)
                list_type = "list_ordered" if re.match(r"^\d+\.", part) else "list_unordered"
                sections.append({
                    "type": list_type,
                    "items": items
                })
            else:
                # 普通文本
                sections.append({
                    "type": "text",
                    "markdown": part.strip()
                })

        return sections

    def _extract_list_items(self, content: str) -> list[dict]:
        """从 markdown 列表中提取项"""
        items = []
        lines = content.split("\n")

        for line in lines:
            if line.strip().startswith("-") or re.match(r"^\d+\.", line):
                # 移除列表符号
                title = re.sub(r"^(-|\d+\.)\s*", "", line).strip()
                if title:
                    items.append({"title": title})

        return items

    async def generate_structured_sections(
        self, question: str, top_k: int = 5
    ) -> StructuredChatResponse:
        """
        非流式版本：等待完整响应后返回
        适合 `/api/chat/structured` 端点
        """
        sections = []
        sources = []
        confidence = 0.85

        async for event in self.stream_with_structure(question, top_k):
            if event["type"] == "sources":
                sources = event.get("sources", [])
                confidence = event.get("confidence", 0.85)
            elif event["type"] == "section":
                sections.append(event["section"])

        return StructuredChatResponse(
            sections=sections,
            sources=[SourceReference(**s) for s in sources] if sources else [],
            confidence=confidence,
            session_id="",
            timestamp=datetime.now(),
            intent="knowledge_qa",
            workflow=[]
        )


# 全局 RAG 服务实例
rag_service = RAGService()
