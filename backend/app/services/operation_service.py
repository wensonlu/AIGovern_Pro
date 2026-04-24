from typing import Any, Optional, AsyncIterator
from datetime import datetime
from app.core.config import settings
from app.core.database import SessionLocal
from sqlalchemy.orm import Session
from app.models.db_models import OperationLog as OperationLogModel, Order, User, Product, ProductPriceHistory
from sqlalchemy import text
import json
import logging

logger = logging.getLogger(__name__)


class OperationService:
    """智能操作执行服务 - A2UI 能力"""

    def __init__(self):
        self.operation_templates = {
            "approve_order": self._approve_order,
            "export_users": self._export_users,
            "process_refund": self._process_refund,
            "batch_update_stock": self._batch_update_stock,
            "update_product_price": self._update_product_price,
        }

    async def execute_operation(
        self, operation_type: str, parameters: dict[str, Any], user_id: int = 1
    ) -> dict[str, Any]:
        """执行智能操作并记录日志"""

        handler = self.operation_templates.get(operation_type)
        if not handler:
            raise ValueError(f"不支持的操作类型: {operation_type}")

        # 创建操作日志
        db = SessionLocal()
        log_entry = OperationLogModel(
            user_id=user_id,
            operation_type=operation_type,
            operation_target=self._get_operation_target(operation_type),
            operation_detail={"parameters": parameters},
            status="pending",
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        try:
            # 执行操作
            result = await handler(parameters, db)
            
            # 更新日志为成功
            log_entry.status = "success"
            log_entry.operation_detail = {
                "parameters": parameters,
                "result": result
            }
            db.commit()

            return {
                "status": "success",
                "operation_id": log_entry.id,
                "operation_type": operation_type,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            # 更新日志为失败
            log_entry.status = "failed"
            log_entry.operation_detail = {
                "parameters": parameters,
                "error": str(e)
            }
            db.commit()

            return {
                "status": "failed",
                "operation_id": log_entry.id,
                "operation_type": operation_type,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            db.close()

    def _get_operation_target(self, operation_type: str) -> str:
        """获取操作目标"""
        targets = {
            "approve_order": "orders",
            "export_users": "users",
            "process_refund": "orders",
            "batch_update_stock": "products",
        }
        return targets.get(operation_type, "unknown")

    async def _approve_order(self, parameters: dict, db: Session) -> dict:
        """批准订单 - 真实数据库操作"""
        order_ids = parameters.get("order_ids", [])
        reason = parameters.get("reason", "")

        if not order_ids:
            # 如果没有指定订单ID，查找所有 pending 状态的订单
            pending_orders = db.query(Order).filter(Order.status == "pending").all()
            order_ids = [o.id for o in pending_orders]

        approved_count = 0
        for order_id in order_ids:
            order = db.query(Order).filter(Order.id == order_id).first()
            if order and order.status == "pending":
                order.status = "approved"
                approved_count += 1

        db.commit()

        return {
            "approved_count": approved_count,
            "order_ids": order_ids,
            "reason": reason,
        }

    async def _export_users(self, parameters: dict, db: Session) -> dict:
        """导出用户 - 真实数据库查询"""
        date_range = parameters.get("date_range", "")
        format_type = parameters.get("format", "csv")

        # 查询用户数据
        users = db.query(User).all()
        user_list = [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]

        return {
            "exported_count": len(user_list),
            "format": format_type,
            "data": user_list,
            "download_url": f"/api/operations/download/users_{datetime.now().timestamp()}.{format_type}",
        }

    async def _process_refund(self, parameters: dict, db: Session) -> dict:
        """处理退款 - 真实数据库操作"""
        order_id = parameters.get("order_id")
        reason = parameters.get("reason", "")

        if not order_id:
            raise ValueError("必须提供订单ID")

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"订单 {order_id} 不存在")

        # 更新订单状态为 refunded
        order.status = "refunded"
        db.commit()

        return {
            "order_id": order_id,
            "refund_status": "processed",
            "refund_amount": order.amount,
            "reason": reason,
        }

    async def _batch_update_stock(self, parameters: dict, db: Session) -> dict:
        """批量更新库存 - 真实数据库操作"""
        updates = parameters.get("updates", [])

        if not updates:
            # 如果没有指定更新，自动为库存小于10的商品补货到20
            result = db.execute(
                text("""
                    UPDATE products 
                    SET stock = 20 
                    WHERE stock < 10 
                    RETURNING id, name, stock
                """)
            )
            updated_rows = result.fetchall()
            db.commit()

            return {
                "updated_count": len(updated_rows),
                "updates": [
                    {"product_id": row.id, "name": row.name, "new_stock": row.stock}
                    for row in updated_rows
                ],
                "message": "自动为低库存商品补货到20",
            }

        # 处理指定的更新
        updated_count = 0
        update_results = []
        for update in updates:
            product_id = update.get("product_id")
            new_stock = update.get("stock")
            
            result = db.execute(
                text("UPDATE products SET stock = :stock WHERE id = :id"),
                {"stock": new_stock, "id": product_id}
            )
            if result.rowcount > 0:
                updated_count += 1
                update_results.append({"product_id": product_id, "new_stock": new_stock})

        db.commit()

        return {
            "updated_count": updated_count,
            "updates": update_results,
        }

    async def _update_product_price(self, parameters: dict, db: Session) -> dict:
        """更新商品价格 - 真实数据库操作，自动记录价格修改历史"""
        product_id = parameters.get("product_id")
        product_name = parameters.get("product_name")
        new_price = parameters.get("new_price")
        changed_by = parameters.get("changed_by", "user")  # 'user' 或 'ai'
        changed_by_id = parameters.get("changed_by_id", 1)
        reason = parameters.get("reason", "价格调整")

        if not new_price:
            raise ValueError("必须提供新价格")

        # 查找商品
        product = None
        if product_id:
            product = db.query(Product).filter(Product.id == product_id).first()
        elif product_name:
            # 尝试精确匹配 SKU（如果输入包含类似 SKU 的格式）
            import re
            sku_match = re.search(r'\b([A-Z]+\d+)\b', product_name)
            if sku_match:
                sku = sku_match.group(1)
                product = db.query(Product).filter(Product.sku.ilike(sku)).first()
            
            # 如果 SKU 匹配失败，尝试按名称查询（去除可能的 SKU 部分）
            if not product:
                # 移除 SKU 部分，保留纯名称
                clean_name = re.sub(r'\s*[A-Z]+\d+\s*', '', product_name).strip()
                if clean_name:
                    product = db.query(Product).filter(Product.name.ilike(f"%{clean_name}%")).first()
            
            # 最后尝试原始名称模糊查询
            if not product:
                product = db.query(Product).filter(Product.name.ilike(f"%{product_name}%")).first()

        if not product:
            raise ValueError(f"商品不存在")

        # 记录旧价格
        old_price = product.price

        # 更新价格
        product.price = new_price

        # 记录价格修改历史
        history = ProductPriceHistory(
            product_id=product.id,
            old_price=old_price,
            new_price=new_price,
            changed_by=changed_by,
            changed_by_id=changed_by_id,
            reason=reason,
        )
        db.add(history)
        db.commit()

        return {
            "updated_count": 1,
            "product_id": product.id,
            "product_name": product.name,
            "old_price": old_price,
            "new_price": new_price,
            "changed_by": changed_by,
            "history_recorded": True,
        }

    async def stream_with_structure(
        self, message: str, operation_result: dict[str, Any]
    ) -> AsyncIterator[dict]:
        """结构化流式处理操作结果"""
        try:
            from app.core.llm import llm_client, LLMServiceError, LLMTimeoutError
            from app.models.schemas import ListOrderedSection, OrderedListItem, TextSection

            # 1. 返回操作结果摘要
            yield {
                "type": "sources",
                "sources": [{
                    "document_id": 0,
                    "title": "智能操作",
                    "filename": "operation",
                    "chunk_index": 0,
                    "relevance": 1.0,
                    "relevance_percentage": "100%",
                    "text_preview": f"操作: {operation_result.get('operation_type', '')}"
                }],
                "confidence": 0.9 if operation_result.get('status') == 'success' else 0.5,
            }

            # 2. 构建结构化 prompt
            prompt = self._build_structured_operation_prompt(message, operation_result)

            # 3. 流式调用 LLM，累积完整响应
            accumulated_content = ""
            try:
                async for chunk in llm_client.stream_text(prompt, max_tokens=1024):
                    accumulated_content += chunk
            except (LLMServiceError, LLMTimeoutError) as e:
                logger.error(f"LLM 流式调用失败: {e}")
                yield {
                    "type": "error",
                    "message": f"LLM 服务错误：{str(e)}"
                }
                return

            # 4. 解析 LLM 输出为 Section 对象
            try:
                sections_data = json.loads(accumulated_content)
                if not isinstance(sections_data, list):
                    sections_data = [sections_data]
            except json.JSONDecodeError:
                logger.warning("LLM 返回的不是有效 JSON，尝试降级处理")
                sections_data = self._parse_markdown_to_sections(accumulated_content)

            # 5. 逐块返回 section
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

            # 6. 完成事件
            yield {
                "type": "done",
                "confidence": 0.9 if operation_result.get('status') == 'success' else 0.5,
            }

        except Exception as e:
            logger.error(f"Error in stream_with_structure: {e}")
            yield {
                "type": "error",
                "message": f"处理失败：{str(e)}"
            }

    def _build_structured_operation_prompt(self, message: str, operation_result: dict) -> str:
        """构建结构化操作 prompt"""
        prompt = f"""用户指令：{message}

操作执行结果：
{json.dumps(operation_result, ensure_ascii=False, indent=2)}

请将操作结果转换为以下 JSON 格式的 sections 数组：

[
  {{
    "type": "text",
    "markdown": "操作执行状态和结果摘要"
  }},
  {{
    "type": "list_ordered",
    "items": [
      {{
        "title": "关键结果",
        "details_markdown": "详细信息"
      }}
    ]
  }}
]

要求：
1. 直接返回 JSON 数组，不要有任何其他文字
2. 如果操作成功，用绿色勾号 ✅ 标记
3. 如果操作失败，用红色叉号 ❌ 标记，并说明原因
4. 用 list_ordered 展示关键的执行步骤和结果
5. 确保返回的 JSON 格式正确
"""
        return prompt

    def _validate_section(self, data: dict) -> "Section":
        """验证并转换原始数据为 Section 对象"""
        from app.models.schemas import ListOrderedSection, OrderedListItem, TextSection, Section

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
                    details_markdown=item.get("details_markdown")
                )
                for item in data.get("items", [])
            ]
            return ListOrderedSection(type="list_ordered", items=items)

        else:
            raise ValueError(f"Unknown section type: {section_type}")

    def _parse_markdown_to_sections(self, content: str) -> list[dict]:
        """降级方案：将 markdown 转换为 sections"""
        import re
        sections = []

        parts = content.split("\n## ")

        for part in parts:
            if not part.strip():
                continue

            if part.strip().startswith("-") or re.match(r"^\d+\.", part):
                items = self._extract_list_items(part)
                list_type = "list_ordered" if re.match(r"^\d+\.", part) else "list_unordered"
                sections.append({
                    "type": list_type,
                    "items": items
                })
            else:
                sections.append({
                    "type": "text",
                    "markdown": part.strip()
                })

        return sections

    def _extract_list_items(self, content: str) -> list[dict]:
        """从 markdown 列表中提取项"""
        import re
        items = []
        lines = content.split("\n")

        for line in lines:
            if line.strip().startswith("-") or re.match(r"^\d+\.", line):
                title = re.sub(r"^(-|\d+\.)\s*", "", line).strip()
                if title:
                    items.append({"title": title})

        return items

    def get_operation_logs(self, db: Session, limit: int = 50) -> list[dict]:
        """获取操作日志列表"""
        logs = db.query(OperationLogModel).order_by(
            OperationLogModel.created_at.desc()
        ).limit(limit).all()

        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "operation_type": log.operation_type,
                "operation_target": log.operation_target,
                "status": log.status,
                "detail": log.operation_detail,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    def get_templates(self) -> list[dict]:
        """获取所有操作模板"""
        return [
            {
                "id": 1,
                "name": "批准订单",
                "description": "批准待审订单",
                "operation_type": "approve_order",
                "required_params": {"order_ids": "list", "reason": "str"},
            },
            {
                "id": 2,
                "name": "导出用户",
                "description": "导出用户列表",
                "operation_type": "export_users",
                "required_params": {"date_range": "str", "format": "str"},
            },
            {
                "id": 3,
                "name": "处理退款",
                "description": "处理订单退款",
                "operation_type": "process_refund",
                "required_params": {"order_id": "int", "reason": "str"},
            },
            {
                "id": 4,
                "name": "更新库存",
                "description": "批量更新商品库存",
                "operation_type": "batch_update_stock",
                "required_params": {"updates": "list"},
            },
            {
                "id": 5,
                "name": "修改价格",
                "description": "修改商品价格",
                "operation_type": "update_product_price",
                "required_params": {"product_id": "int", "new_price": "float"},
            },
        ]


operation_service = OperationService()
