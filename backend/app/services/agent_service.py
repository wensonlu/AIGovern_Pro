"""
智能代理服务 - 意图识别与工具调用
支持：知识问答(RAG)、数据查询(SQL)、智能操作(Operation)、经营诊断(Diagnosis)
"""

from typing import Optional, Literal
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.llm import llm_client
from app.services.rag_service import RAGService
from app.services.sql_service import sql_service
from app.services.operation_service import operation_service
from app.services.diagnosis_service import diagnosis_service
from app.models.schemas import ChatResponse, SourceReference
from app.models.db_models import Order, User, Product
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
        elif intent == "business_diagnosis":
            return await self._handle_business_diagnosis(message, db, session_id)
        else:  # knowledge_qa
            return await self._handle_knowledge_qa(message, session_id)

    async def _recognize_intent(
        self, message: str
    ) -> Literal["knowledge_qa", "data_query", "smart_operation", "business_diagnosis"]:
        """
        使用 LLM 识别用户意图
        """
        prompt = f"""请分析用户的输入，判断用户想要执行的操作类型。

用户输入："{message}"

可选的意图类型：
1. knowledge_qa - 知识问答（询问公司政策、流程、文档内容等）
2. data_query - 数据查询（询问用户、订单、商品、统计数据等具体数值）
3. smart_operation - 智能操作（修改数据、执行操作、更新状态等）
4. business_diagnosis - 经营诊断（分析指标是否正常、诊断问题、生成报告、询问"为什么"等）

判断规则：
- 如果用户问"有多少用户"、"员工信息"、"人员列表"、"订单数据"、"查询..." → data_query
- 如果用户说"修改..."、"更新..."、"删除..."、"批准..." → smart_operation
- 如果用户问"...是否正常"、"为什么..."、"分析..."、"诊断..."、"经营状况" → business_diagnosis
- 其他情况 → knowledge_qa

只返回意图类型，不要其他解释："""

        try:
            response = await self.llm.generate_text(prompt, max_tokens=50)
            response = response.strip().lower()

            if "data_query" in response or "数据查询" in response:
                return "data_query"
            elif "smart_operation" in response or "智能操作" in response or "操作" in response:
                return "smart_operation"
            elif "business_diagnosis" in response or "经营诊断" in response or "诊断" in response:
                return "business_diagnosis"
            else:
                return "knowledge_qa"
        except Exception as e:
            print(f"⚠️ 意图识别失败，默认使用知识问答: {e}")
            # 降级到关键词匹配
            if self._is_diagnosis_question(message):
                return "business_diagnosis"
            return "knowledge_qa"
    
    def _is_diagnosis_question(self, message: str) -> bool:
        """通过关键词判断是否为诊断问题（降级方案）"""
        diagnosis_keywords = [
            "是否正常", "为什么", "怎么回事", "分析", "诊断",
            "经营状况", "经营情况", "业绩", "问题", "异常",
            "下降", "下滑", "不好", "差", "如何改进", "建议"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in diagnosis_keywords)

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

    async def _handle_business_diagnosis(
        self, message: str, db: Session, session_id: Optional[str]
    ) -> ChatResponse:
        """处理经营诊断意图"""
        try:
            # 1. 计算真实业务指标
            metrics = await self._calculate_metrics(db)
            
            # 2. 分析指标，识别问题
            analysis = await diagnosis_service.analyze_metrics(metrics)
            
            # 3. 根据用户问题生成针对性回答
            answer = await self._generate_diagnosis_answer(message, metrics, analysis)

            return ChatResponse(
                answer=answer,
                sources=[SourceReference(
                    document_id=0,
                    title="经营诊断",
                    filename="diagnosis",
                    chunk_index=0,
                    relevance=1.0,
                    relevance_percentage="100%",
                    text_preview=f"指标分析: {len(analysis['issues'])} 个问题"
                )],
                confidence=0.92,
                session_id=session_id or "default",
                timestamp=datetime.now(),
            )
        except Exception as e:
            print(f"诊断失败: {e}")
            return ChatResponse(
                answer=f"经营诊断分析失败：{str(e)}",
                sources=[],
                confidence=0.0,
                session_id=session_id or "default",
                timestamp=datetime.now(),
            )
    
    async def _calculate_metrics(self, db: Session) -> dict:
        """计算真实业务指标"""
        # 订单总数
        order_count = db.query(func.count(Order.id)).scalar() or 0
        
        # GMV
        gmv = db.query(func.sum(Order.amount)).scalar() or 0.0
        
        # 用户总数
        total_users = db.query(func.count(User.id)).scalar() or 0
        
        # 活跃用户（有订单的用户）
        active_users = db.query(func.count(func.distinct(Order.user_id))).scalar() or 0
        
        # 转化率
        conversion_rate = (active_users / total_users * 100) if total_users > 0 else 0
        
        # 客单价
        avg_order_value = (gmv / order_count) if order_count > 0 else 0
        
        # 库存紧张商品
        low_stock_count = db.query(func.count(Product.id)).filter(Product.stock < 10).scalar() or 0
        
        return {
            "order_count": order_count,
            "gmv": round(gmv, 2),
            "conversion_rate": round(conversion_rate, 2),
            "active_users": active_users,
            "total_users": total_users,
            "avg_order_value": round(avg_order_value, 2),
            "low_stock_count": low_stock_count,
        }
    
    async def _generate_diagnosis_answer(self, message: str, metrics: dict, analysis: dict) -> str:
        """生成诊断回答"""
        message_lower = message.lower()
        
        # 根据问题类型生成针对性回答
        if "订单" in message_lower or "order" in message_lower:
            return self._format_order_diagnosis(metrics, analysis)
        elif "用户" in message_lower or "user" in message_lower:
            return self._format_user_diagnosis(metrics, analysis)
        elif "转化" in message_lower or "conversion" in message_lower:
            return self._format_conversion_diagnosis(metrics, analysis)
        elif "gmv" in message_lower or "营收" in message_lower or "销售额" in message_lower:
            return self._format_gmv_diagnosis(metrics, analysis)
        else:
            # 综合诊断
            return self._format_comprehensive_diagnosis(metrics, analysis)
    
    def _format_order_diagnosis(self, metrics: dict, analysis: dict) -> str:
        """格式化订单诊断"""
        order_count = metrics["order_count"]
        is_normal = order_count >= 500
        
        answer = f"📊 **订单量诊断**\n\n"
        answer += f"当前订单总数：**{order_count}** 单\n"
        answer += f"判断标准：{'✅ 正常' if is_normal else '⚠️ 偏低'}（阈值：500单）\n\n"
        
        if not is_normal:
            answer += "**问题分析**：\n"
            answer += "- 订单量低于预期，可能影响整体营收\n"
            answer += "- 建议开展促销活动提升订单量\n"
            answer += "- 优化产品推荐算法，提高转化率\n"
        else:
            answer += "**结论**：订单量处于正常水平，继续保持！\n"
        
        answer += f"\n客单价：**{metrics['avg_order_value']}** 元"
        return answer
    
    def _format_user_diagnosis(self, metrics: dict, analysis: dict) -> str:
        """格式化用户诊断"""
        active_users = metrics["active_users"]
        total_users = metrics["total_users"]
        is_normal = active_users >= 3000
        
        answer = f"👥 **用户活跃度诊断**\n\n"
        answer += f"总用户数：**{total_users}** 人\n"
        answer += f"活跃用户数：**{active_users}** 人\n"
        answer += f"判断标准：{'✅ 正常' if is_normal else '⚠️ 偏低'}（阈值：3000人）\n\n"
        
        if not is_normal:
            answer += "**问题分析**：\n"
            answer += "- 活跃用户数低于预期\n"
            answer += "- 建议加强用户运营，提升产品粘性\n"
            answer += "- 开展拉新活动，扩大用户基础\n"
        else:
            answer += "**结论**：用户活跃度良好！\n"
        
        return answer
    
    def _format_conversion_diagnosis(self, metrics: dict, analysis: dict) -> str:
        """格式化转化率诊断"""
        conversion_rate = metrics["conversion_rate"]
        is_normal = conversion_rate >= 2.0
        
        answer = f"🔄 **转化率诊断**\n\n"
        answer += f"当前转化率：**{conversion_rate}%**\n"
        answer += f"判断标准：{'✅ 正常' if is_normal else '⚠️ 偏低'}（阈值：2%）\n\n"
        
        if not is_normal:
            answer += "**问题分析**：\n"
            answer += "- 转化率低于行业平均水平\n"
            answer += "- 可能存在用户体验或产品吸引力问题\n"
            answer += "- 建议优化产品页面、简化购买流程\n"
        else:
            answer += "**结论**：转化率处于正常水平！\n"
        
        return answer
    
    def _format_gmv_diagnosis(self, metrics: dict, analysis: dict) -> str:
        """格式化GMV诊断"""
        gmv = metrics["gmv"]
        order_count = metrics["order_count"]
        avg_order = metrics["avg_order_value"]
        
        answer = f"💰 **营收诊断(GMV)**\n\n"
        answer += f"总交易额：**{gmv:.2f}** 元\n"
        answer += f"订单数：**{order_count}** 单\n"
        answer += f"客单价：**{avg_order:.2f}** 元\n\n"
        
        if order_count > 0:
            answer += "**分析**：\n"
            if avg_order < 100:
                answer += "- 客单价偏低，建议推出满减活动提升客单价\n"
            answer += "- 可以通过提升订单量或客单价来增加GMV\n"
        
        return answer
    
    def _format_comprehensive_diagnosis(self, metrics: dict, analysis: dict) -> str:
        """格式化综合诊断"""
        issues = analysis["issues"]
        
        answer = f"📈 **经营状况综合诊断**\n\n"
        answer += "**核心指标**：\n"
        answer += f"- 订单总数：{metrics['order_count']} 单\n"
        answer += f"- 总交易额：{metrics['gmv']:.2f} 元\n"
        answer += f"- 活跃用户：{metrics['active_users']} 人\n"
        answer += f"- 转化率：{metrics['conversion_rate']}%\n"
        answer += f"- 客单价：{metrics['avg_order_value']:.2f} 元\n\n"
        
        if issues:
            answer += f"**发现 {len(issues)} 个问题**：\n"
            for issue in issues:
                severity_emoji = "🔴" if issue["severity"] == "high" else "🟡"
                answer += f"{severity_emoji} {issue['issue']}（当前：{issue['current']}，阈值：{issue['threshold']}）\n"
            answer += "\n建议关注上述问题并采取改进措施。"
        else:
            answer += "✅ **结论**：所有指标正常，经营状况良好！"
        
        if metrics["low_stock_count"] > 0:
            answer += f"\n\n⚠️ 提醒：有 **{metrics['low_stock_count']}** 个商品库存紧张，请及时补货。"
        
        return answer

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
