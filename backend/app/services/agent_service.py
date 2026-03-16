"""
智能代理服务 - 意图识别与工具调用
支持：知识问答(RAG)、数据查询(SQL)、智能操作(Operation)
"""

from typing import Optional, Literal
from sqlalchemy.orm import Session
from app.core.llm import llm_client
from app.services.rag_service import RAGService
from app.services.sql_service import sql_service
from app.services.operation_service import operation_service
from app.models.schemas import ChatResponse, SourceReference
from datetime import datetime
import json
import re


class AgentService:
    """智能代理服务 - 统一处理用户对话"""

    def __init__(self):
        self.llm = llm_client
        self.rag = RAGService()

    async def process_message(
        self,
        message: str,
        db: Session,
        session_id: Optional[str] = None
    ) -> ChatResponse:
        """
        处理用户消息，自动识别意图并调用相应工具
        """
        # 第一步：意图识别
        intent = await self._recognize_intent(message)
        print(f"🎯 识别到的意图: {intent}")

        # 第二步：根据意图路由到相应处理逻辑
        if intent == "data_query":
            return await self._handle_data_query(message, db, session_id)
        elif intent == "smart_operation":
            return await self._handle_smart_operation(message, db, session_id)
        else:  # knowledge_qa
            return await self._handle_knowledge_qa(message, session_id)

    async def _recognize_intent(
        self, message: str
    ) -> Literal["knowledge_qa", "data_query", "smart_operation"]:
        """
        使用 LLM 识别用户意图
        """
        prompt = f"""请分析用户的输入，判断用户想要执行的操作类型。

用户输入："{message}"

可选的意图类型：
1. knowledge_qa - 知识问答（询问公司政策、流程、文档内容等）
2. data_query - 数据查询（询问用户、订单、商品、统计数据等）
3. smart_operation - 智能操作（修改数据、执行操作、更新状态等）

判断规则：
- 如果用户问"有多少用户"、"订单数据"、"查询..." → data_query
- 如果用户说"修改..."、"更新..."、"删除..."、"批准..." → smart_operation
- 其他情况 → knowledge_qa

只返回意图类型，不要其他解释："""

        try:
            response = await self.llm.generate_text(prompt, max_tokens=50)
            response = response.strip().lower()

            if "data_query" in response or "数据查询" in response:
                return "data_query"
            elif "smart_operation" in response or "智能操作" in response or "操作" in response:
                return "smart_operation"
            else:
                return "knowledge_qa"
        except Exception as e:
            print(f"⚠️ 意图识别失败，默认使用知识问答: {e}")
            return "knowledge_qa"

    async def _handle_data_query(
        self, message: str, db: Session, session_id: Optional[str]
    ) -> ChatResponse:
        """处理数据查询意图"""
        try:
            # 生成并执行 SQL
            sql, chart_type = await sql_service.generate_sql(message)
            result = await sql_service.execute_query(sql, db)

            # 构建自然语言回答
            if result:
                result_summary = f"查询到 {len(result)} 条数据"
                result_preview = json.dumps(result[:3], ensure_ascii=False, indent=2)
            else:
                result_summary = "未查询到数据"
                result_preview = "[]"

            answer_prompt = f"""用户询问数据："{message}"

执行的SQL：{sql}

查询结果：{result_summary}
数据预览：{result_preview}

请用自然语言总结查询结果，用中文回答："""

            answer = await self.llm.generate_text(answer_prompt, max_tokens=512)

            return ChatResponse(
                answer=answer,
                sources=[SourceReference(
                    document_id=0,
                    title="数据查询",
                    filename="database",
                    chunk_index=0,
                    relevance=1.0,
                    relevance_percentage="100%",
                    text_preview=f"SQL: {sql[:100]}..."
                )],
                confidence=0.95,
                session_id=session_id or "default",
                timestamp=datetime.now(),
            )
        except Exception as e:
            return ChatResponse(
                answer=f"数据查询失败：{str(e)}",
                sources=[],
                confidence=0.0,
                session_id=session_id or "default",
                timestamp=datetime.now(),
            )

    async def _handle_smart_operation(
        self, message: str, db: Session, session_id: Optional[str]
    ) -> ChatResponse:
        """处理智能操作意图"""
        try:
            # 解析操作类型和参数
            operation_type, parameters = await self._parse_operation(message)

            if not operation_type:
                return ChatResponse(
                    answer="抱歉，我无法理解您要执行的操作。请尝试用更明确的表述，比如：\n- 批准所有待审订单\n- 修改笔记本电脑价格为1元\n- 导出用户列表",
                    sources=[],
                    confidence=0.0,
                    session_id=session_id or "default",
                    timestamp=datetime.now(),
                )

            # 执行操作
            result = await operation_service.execute_operation(
                operation_type, parameters
            )

            # 构建回答
            if result.get("status") == "success":
                answer = f"✅ 操作执行成功！\n\n操作类型：{operation_type}\n"
                if "result" in result:
                    result_data = result["result"]
                    if isinstance(result_data, dict):
                        for key, value in result_data.items():
                            if key != "data":  # 不显示完整数据
                                answer += f"- {key}: {value}\n"
            else:
                answer = f"❌ 操作执行失败：{result.get('error', '未知错误')}"

            return ChatResponse(
                answer=answer,
                sources=[SourceReference(
                    document_id=0,
                    title="智能操作",
                    filename="operation",
                    chunk_index=0,
                    relevance=1.0,
                    relevance_percentage="100%",
                    text_preview=f"操作: {operation_type}"
                )],
                confidence=0.9,
                session_id=session_id or "default",
                timestamp=datetime.now(),
            )
        except Exception as e:
            return ChatResponse(
                answer=f"操作执行失败：{str(e)}",
                sources=[],
                confidence=0.0,
                session_id=session_id or "default",
                timestamp=datetime.now(),
            )

    async def _parse_operation(self, message: str) -> tuple[Optional[str], dict]:
        """
        解析用户消息，提取操作类型和参数
        """
        message_lower = message.lower()
        parameters = {}

        # 匹配各种操作类型
        if "批准" in message or "审批" in message:
            operation_type = "approve_order"
            # 尝试提取订单ID
            order_ids = re.findall(r'\d+', message)
            if order_ids:
                parameters["order_ids"] = [int(x) for x in order_ids]

        elif "导出" in message or "下载" in message:
            operation_type = "export_users"
            if "json" in message_lower:
                parameters["format"] = "json"
            else:
                parameters["format"] = "csv"

        elif "退款" in message or "退货" in message:
            operation_type = "process_refund"
            order_ids = re.findall(r'\d+', message)
            if order_ids:
                parameters["order_id"] = int(order_ids[0])
            parameters["reason"] = "用户申请退款"

        elif "库存" in message or "补货" in message:
            operation_type = "batch_update_stock"
            # 自动模式，不传参数

        elif "修改" in message or "更新" in message:
            # 智能识别修改类型
            if "价格" in message or "金额" in message or "元" in message:
                # 提取商品名称和价格
                # 匹配模式：修改[商品名]价格为[数字]元 或 修改[商品名]价格到[数字]
                match = re.search(r'(?:修改|更新)\s*(.+?)\s*(?:价格)?\s*(?:为|到|改成)?\s*(\d+)\s*(?:元|块)?', message)
                if match:
                    product_name = match.group(1).strip()
                    new_price = float(match.group(2))
                    parameters["product_name"] = product_name
                    parameters["new_price"] = new_price
                    parameters["changed_by"] = "ai"  # 标记为AI操作
                    parameters["changed_by_id"] = 0  # AI操作的ID设为0
                    parameters["reason"] = f"AI助手根据用户指令修改: {message[:50]}"
                    operation_type = "update_product_price"
                else:
                    operation_type = None
            else:
                operation_type = None
        else:
            operation_type = None

        return operation_type, parameters

    async def _handle_knowledge_qa(
        self, message: str, session_id: Optional[str]
    ) -> ChatResponse:
        """处理知识问答意图 - 使用原有的 RAG 逻辑"""
        return await self.rag.process_query(message, session_id)


# 全局代理服务实例
agent_service = AgentService()
