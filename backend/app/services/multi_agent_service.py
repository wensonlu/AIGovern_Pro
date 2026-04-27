"""
多Agent协作服务 - 处理复杂意图
支持多个意图的检测和并行执行，自动合并结果
"""

from typing import AsyncIterator, Optional, Any
from sqlalchemy.orm import Session
from app.core.llm import llm_client
from app.services.rag_service import RAGService
from app.services.sql_service import sql_service
from app.services.diagnosis_service import diagnosis_service
from app.models.schemas import ChatResponse, SourceReference
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ComplexIntentAnalysis:
    """复杂意图分析结果"""
    def __init__(self):
        self.intents: list[str] = []  # [data_query, business_diagnosis, ...]
        self.is_complex: bool = False
        self.main_intent: str = ""
        self.sub_intents: list[str] = []


class MultiAgentService:
    """多Agent服务 - 处理复杂意图"""

    def __init__(self):
        self.llm = llm_client
        self.rag = RAGService()

    async def analyze_complex_intent(self, message: str) -> ComplexIntentAnalysis:
        """
        分析用户消息是否包含复杂意图（多个意图组合）

        例如：
        - "我们最近3个月的订单趋势如何？预测下个月会不会继续下降？有哪些改进建议？"
          → data_query（查询趋势） + business_diagnosis（诊断问题） + knowledge_qa（获取建议）

        - "今天我们处理了多少订单？这个数字是否正常？需要采取什么行动？"
          → data_query（订单数量） + business_diagnosis（是否正常） + knowledge_qa（行动建议）
        """
        logger.info(f"[多Agent分析] 开始分析复杂意图: {message[:50]}...")

        prompt = f"""分析用户输入是否涉及多个意图，并提取所有意图。

用户输入："{message}"

可能的意图类型：
1. knowledge_qa - 知识问答（询问政策、流程、文档、建议等）
2. data_query - 数据查询（查询具体数值、统计、趋势等）
3. smart_operation - 智能操作（修改数据、执行操作、审批等）
4. business_diagnosis - 经营诊断（分析是否正常、诊断问题、预测等）

要求：
1. 识别所有涉及的意图
2. 标记主要意图（最重要的那个）
3. 标记子意图（辅助的其他意图）
4. 用JSON格式返回

返回格式：
{{
  "is_complex": true/false,
  "main_intent": "意图类型",
  "intents": ["意图1", "意图2", ...]
}}

只返回JSON，不要其他解释："""

        try:
            response = await self.llm.generate_text(prompt, max_tokens=200)
            result = json.loads(response.strip())

            analysis = ComplexIntentAnalysis()
            analysis.is_complex = result.get("is_complex", False)
            analysis.main_intent = result.get("main_intent", "knowledge_qa")
            analysis.intents = result.get("intents", [])

            if len(analysis.intents) > 1:
                analysis.sub_intents = [i for i in analysis.intents if i != analysis.main_intent]

            logger.info(f"[多Agent分析完成] 是否复杂: {analysis.is_complex}, "
                       f"主意图: {analysis.main_intent}, 子意图: {analysis.sub_intents}")
            return analysis

        except Exception as e:
            logger.error(f"[多Agent分析] 意图分析失败: {e}")
            # 降级到单意图识别
            analysis = ComplexIntentAnalysis()
            analysis.is_complex = False
            analysis.main_intent = "knowledge_qa"
            return analysis

    async def process_complex_message(
        self,
        message: str,
        db: Session,
        session_id: Optional[str] = None,
        top_k: int = 5,
    ) -> ChatResponse:
        """
        处理复杂意图消息 - 多Agent并行执行

        流程：
        1. 分析意图（检测是否复杂）
        2. 如果复杂：并行执行多个Agent，合并结果
        3. 如果单一：使用原有流程
        """
        logger.info(f"[多Agent处理] 开始处理消息: {message[:50]}...")

        # 1. 分析意图
        analysis = await self.analyze_complex_intent(message)

        # 2. 单一意图 - 使用原有流程
        if not analysis.is_complex:
            logger.info(f"[多Agent处理] 单一意图 {analysis.main_intent}，使用原流程")
            from app.services.agent_service import agent_service
            return await agent_service.process_message(message, db, session_id)

        # 3. 复杂意图 - 多Agent并行处理
        logger.info(f"[多Agent处理] 检测到复杂意图，启动多Agent并行处理")
        logger.info(f"[多Agent处理] 主意图: {analysis.main_intent}, 子意图: {analysis.sub_intents}")

        # 并行执行各Agent
        agent_results = {}

        # 执行主意图Agent
        if analysis.main_intent == "data_query":
            logger.info(f"[多Agent处理] 执行Agent: data_query")
            agent_results["data_query"] = await self._execute_data_query(message, db)
        elif analysis.main_intent == "business_diagnosis":
            logger.info(f"[多Agent处理] 执行Agent: business_diagnosis")
            agent_results["business_diagnosis"] = await self._execute_diagnosis(message, db)
        elif analysis.main_intent == "knowledge_qa":
            logger.info(f"[多Agent处理] 执行Agent: knowledge_qa")
            agent_results["knowledge_qa"] = await self._execute_rag(message, top_k)

        # 执行子意图Agent
        for intent in analysis.sub_intents:
            logger.info(f"[多Agent处理] 执行Agent: {intent}")
            if intent == "data_query":
                agent_results["data_query"] = await self._execute_data_query(message, db)
            elif intent == "business_diagnosis":
                agent_results["business_diagnosis"] = await self._execute_diagnosis(message, db)
            elif intent == "knowledge_qa":
                agent_results["knowledge_qa"] = await self._execute_rag(message, top_k)

        # 4. 合并Agent结果
        logger.info(f"[多Agent处理] 开始合并结果，收集 {len(agent_results)} 个Agent的输出")
        merged_response = await self._merge_agent_results(message, agent_results, analysis)

        logger.info(f"[多Agent处理] 完成，返回合并结果")
        return merged_response

    async def _execute_data_query(self, message: str, db: Session) -> dict:
        """执行数据查询Agent"""
        try:
            logger.info(f"[数据查询Agent] 开始执行...")
            sql, chart_type = await sql_service.generate_sql(message)
            result = await sql_service.execute_query(sql, db)

            logger.info(f"[数据查询Agent] 完成，获得 {len(result)} 条数据")
            return {
                "type": "data_query",
                "sql": sql,
                "data": result,
                "count": len(result),
            }
        except Exception as e:
            logger.error(f"[数据查询Agent] 执行失败: {e}")
            return {"type": "data_query", "error": str(e)}

    async def _execute_diagnosis(self, message: str, db: Session) -> dict:
        """执行诊断Agent"""
        try:
            logger.info(f"[诊断Agent] 开始执行...")
            from app.services.agent_service import agent_service
            metrics = await agent_service._calculate_metrics(db)
            analysis = await diagnosis_service.analyze_metrics(metrics)

            logger.info(f"[诊断Agent] 完成，识别 {analysis['total_issues']} 个问题")
            return {
                "type": "business_diagnosis",
                "metrics": metrics,
                "issues": analysis["issues"],
                "issue_count": analysis["total_issues"],
            }
        except Exception as e:
            logger.error(f"[诊断Agent] 执行失败: {e}")
            return {"type": "business_diagnosis", "error": str(e)}

    async def _execute_rag(self, message: str, top_k: int) -> dict:
        """执行知识问答Agent"""
        try:
            logger.info(f"[RAG Agent] 开始执行...")
            docs = await self.rag.retrieve_documents(message, top_k)

            logger.info(f"[RAG Agent] 完成，检索到 {len(docs)} 个相关文档")
            return {
                "type": "knowledge_qa",
                "documents": docs,
                "doc_count": len(docs),
            }
        except Exception as e:
            logger.error(f"[RAG Agent] 执行失败: {e}")
            return {"type": "knowledge_qa", "error": str(e)}

    async def _merge_agent_results(
        self,
        message: str,
        agent_results: dict[str, dict],
        analysis: ComplexIntentAnalysis,
    ) -> ChatResponse:
        """
        合并多个Agent的结果

        合并策略：
        1. 收集所有数据
        2. 用LLM生成统一回答
        3. 合并source references
        """
        logger.info(f"[合并] 开始合并 {len(agent_results)} 个Agent的结果")

        # 1. 构建合并prompt
        context = self._build_merge_context(agent_results)

        merge_prompt = f"""用户问题: "{message}"

已执行的分析:
{context}

请基于上述所有分析结果，生成一个综合回答。要求：
1. 整合所有Agent的输出
2. 逻辑清晰，避免重复
3. 突出主要结论
4. 提供可行的建议

使用中文回答："""

        logger.info(f"[合并] 调用LLM生成综合回答...")
        answer = await self.llm.generate_text(merge_prompt, max_tokens=1024)

        # 2. 收集所有sources
        sources = self._collect_all_sources(agent_results)

        # 3. 计算置信度（多Agent平均）
        confidence = self._calculate_merged_confidence(agent_results)

        logger.info(f"[合并] 完成，置信度: {confidence:.2%}")

        return ChatResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            session_id="",
            timestamp=datetime.now(),
        )

    def _build_merge_context(self, agent_results: dict[str, dict]) -> str:
        """构建合并上下文"""
        context_parts = []

        if "data_query" in agent_results and "error" not in agent_results["data_query"]:
            result = agent_results["data_query"]
            context_parts.append(f"""
【数据查询结果】
- SQL: {result.get('sql', 'N/A')}
- 数据行数: {result.get('count', 0)}
- 前3条示例: {json.dumps(result.get('data', [])[:3], ensure_ascii=False)}
""")

        if "business_diagnosis" in agent_results and "error" not in agent_results["business_diagnosis"]:
            result = agent_results["business_diagnosis"]
            context_parts.append(f"""
【诊断分析结果】
- 发现问题数: {result.get('issue_count', 0)}
- 核心指标: {json.dumps(result.get('metrics', {}), ensure_ascii=False)}
- 具体问题: {json.dumps(result.get('issues', []), ensure_ascii=False)}
""")

        if "knowledge_qa" in agent_results and "error" not in agent_results["knowledge_qa"]:
            result = agent_results["knowledge_qa"]
            context_parts.append(f"""
【知识库检索结果】
- 相关文档数: {result.get('doc_count', 0)}
- 文档标题: {[d.get('title', 'N/A') for d in result.get('documents', [])]}
""")

        return "\n".join(context_parts)

    def _collect_all_sources(self, agent_results: dict[str, dict]) -> list[SourceReference]:
        """收集所有Agent的sources"""
        sources = []

        # 从知识库检索收集sources
        if "knowledge_qa" in agent_results and "documents" in agent_results["knowledge_qa"]:
            for doc in agent_results["knowledge_qa"]["documents"][:3]:  # 最多3个
                sources.append(SourceReference(
                    document_id=doc.get("document_id", 0),
                    title=doc.get("title", "未知"),
                    filename=doc.get("filename", ""),
                    chunk_index=doc.get("chunk_index", 0),
                    relevance=doc.get("relevance", 0),
                    relevance_percentage=f"{int(doc.get('relevance', 0) * 100)}%",
                    text_preview=doc.get("text", "")[:100],
                ))

        # 从数据查询收集sources
        if "data_query" in agent_results and "sql" in agent_results["data_query"]:
            sources.append(SourceReference(
                document_id=0,
                title="数据查询",
                filename="database",
                chunk_index=0,
                relevance=1.0,
                relevance_percentage="100%",
                text_preview=f"SQL: {agent_results['data_query']['sql'][:80]}...",
            ))

        # 从诊断分析收集sources
        if "business_diagnosis" in agent_results and "metrics" in agent_results["business_diagnosis"]:
            sources.append(SourceReference(
                document_id=0,
                title="经营诊断",
                filename="metrics",
                chunk_index=0,
                relevance=1.0,
                relevance_percentage="100%",
                text_preview="业务指标分析",
            ))

        return sources

    def _calculate_merged_confidence(self, agent_results: dict[str, dict]) -> float:
        """计算合并后的置信度"""
        confidences = []

        # 数据查询的置信度
        if "data_query" in agent_results and "error" not in agent_results["data_query"]:
            confidences.append(0.95)

        # 诊断分析的置信度
        if "business_diagnosis" in agent_results and "error" not in agent_results["business_diagnosis"]:
            confidences.append(0.92)

        # 知识库的置信度
        if "knowledge_qa" in agent_results and "doc_count" in agent_results["knowledge_qa"]:
            doc_count = agent_results["knowledge_qa"]["doc_count"]
            # 文档越多，置信度越高
            confidence = min(0.90, 0.7 + (doc_count / 10) * 0.2)
            confidences.append(confidence)

        # 返回平均置信度
        return sum(confidences) / len(confidences) if confidences else 0.5


# 全局多Agent服务实例
multi_agent_service = MultiAgentService()
