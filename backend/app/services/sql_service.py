from typing import Optional, Any, AsyncIterator
from app.core.llm import llm_client, LLMServiceError, LLMTimeoutError
from app.models.schemas import TextSection, ListOrderedSection, OrderedListItem, Section
from sqlalchemy import text
from sqlalchemy.orm import Session
import json
import logging

logger = logging.getLogger(__name__)


class SQLService:
    """SQL 生成与查询执行服务"""

    def __init__(self):
        self.llm = llm_client

    async def generate_sql(self, natural_query: str, schema_context: Optional[str] = None) -> tuple[str, str]:
        """从自然语言生成 SQL"""

        schema = schema_context or self._get_default_schema()

        # 如果没有 LLM API Key，直接使用示例 SQL
        if not self.llm.api_key:
            chart_type = self._infer_chart_type(natural_query)
            example_sql = self._get_example_sql(natural_query)
            return example_sql, chart_type

        prompt = f"""你是一个 SQL 专家。根据以下数据库 schema 和自然语言查询，生成准确的 SQL 语句。

数据库 schema：
{schema}

自然语言查询：{natural_query}

要求：
1. 只返回 SQL 语句，不要有其他说明
2. SQL 必须与 schema 完全匹配
3. 优先使用 SELECT 查询
4. 如果需要聚合，使用 GROUP BY

返回格式：
SELECT ... FROM ... WHERE ...
"""

        sql = await self.llm.generate_text(prompt, max_tokens=512)
        chart_type = self._infer_chart_type(natural_query)

        # 简单的安全检查 - 只允许 SELECT 查询
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            # 回退到示例SQL
            sql = self._get_example_sql(natural_query)

        return sql.strip(), chart_type

    async def execute_query(self, sql: str, db: Session) -> list[dict]:
        """执行 SQL 查询"""
        try:
            # 安全性检查：只允许 SELECT
            sql_upper = sql.strip().upper()
            if not sql_upper.startswith("SELECT"):
                raise ValueError("只允许执行 SELECT 查询")

            # 执行查询
            result = db.execute(text(sql))
            rows = result.fetchall()

            # 转换为字典列表，处理 datetime 类型
            if rows:
                columns = result.keys()
                processed_rows = []
                for row in rows:
                    row_dict = {}
                    for key, value in zip(columns, row):
                        # 处理 datetime 类型
                        if hasattr(value, 'isoformat'):
                            row_dict[key] = value.isoformat()
                        else:
                            row_dict[key] = value
                    processed_rows.append(row_dict)
                return processed_rows
            return []
        except Exception as e:
            raise RuntimeError(f"SQL 执行失败: {e}")

    def _infer_chart_type(self, query: str) -> str:
        """根据查询内容推断图表类型"""
        query_lower = query.lower()

        if "比较" in query_lower or "对比" in query_lower:
            return "bar"
        elif "趋势" in query_lower or "时间" in query_lower:
            return "line"
        elif "占比" in query_lower or "比例" in query_lower:
            return "pie"
        elif "分布" in query_lower:
            return "scatter"
        else:
            return "table"

    def _get_example_sql(self, query: str) -> str:
        """根据查询获取示例 SQL"""
        query_lower = query.lower()

        # 时间范围查询（最近N天）
        if "最近" in query_lower or "近" in query_lower or "趋势" in query_lower:
            # 提取天数，默认7天
            import re
            days_match = re.search(r'(\d+)\s*天', query_lower)
            days = days_match.group(1) if days_match else "7"
            
            if "gmv" in query_lower or "金额" in query_lower or "营收" in query_lower:
                return f"SELECT DATE(created_at) as date, SUM(amount) as gmv FROM orders WHERE created_at >= CURRENT_DATE - INTERVAL '{days} days' GROUP BY DATE(created_at) ORDER BY date"
            else:
                # 默认返回订单趋势
                return f"SELECT DATE(created_at) as date, COUNT(*) as order_count FROM orders WHERE created_at >= CURRENT_DATE - INTERVAL '{days} days' GROUP BY DATE(created_at) ORDER BY date"
        
        if "订单" in query_lower and ("总数" in query_lower or "数量" in query_lower):
            return "SELECT COUNT(*) as total_orders, DATE(created_at) as date FROM orders GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 10"
        elif "gmv" in query_lower or "金额" in query_lower:
            return "SELECT SUM(amount) as total_gmv, DATE(created_at) as date FROM orders GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 10"
        elif "转化率" in query_lower or "conversion" in query_lower:
            return "SELECT COUNT(DISTINCT user_id) as unique_users, COUNT(*) as total_orders FROM orders"
        elif "用户" in query_lower or "员工" in query_lower or "人员" in query_lower or "入职" in query_lower:
            return "SELECT id, name, email, role, created_at FROM users LIMIT 20"
        elif "商品" in query_lower:
            return "SELECT id, name, sku, price, stock, category FROM products LIMIT 20"
        else:
            return "SELECT id, amount, status, created_at FROM orders LIMIT 20"

    def _get_default_schema(self) -> str:
        """获取默认数据库 schema"""
        return """
-- 订单表
CREATE TABLE orders (
  id INT PRIMARY KEY,
  user_id INT,
  product_id INT,
  quantity INT,
  amount DECIMAL(10,2),
  status VARCHAR(50),
  created_at TIMESTAMP
);

-- 商品表
CREATE TABLE products (
  id INT PRIMARY KEY,
  name VARCHAR(100),
  sku VARCHAR(50),
  price DECIMAL(10,2),
  stock INT,
  category VARCHAR(50),
  created_at TIMESTAMP
);

-- 用户表（存储员工/人员信息）
CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(100),      -- 员工姓名
  email VARCHAR(100),     -- 邮箱
  role VARCHAR(50),       -- 角色/职位
  created_at TIMESTAMP    -- 入职时间
);

-- 指标表
CREATE TABLE metrics (
  id INT PRIMARY KEY,
  metric_name VARCHAR(100),
  metric_date DATE,
  metric_value DECIMAL(12,2),
  dimension_1 VARCHAR(100)
);
"""


    async def stream_with_structure(
        self, message: str, db: Session, top_k: int = 5
    ) -> AsyncIterator[dict]:
        """结构化流式处理数据查询 - 自动转换查询结果为 sections"""
        logger.info(f"[SQL流式处理] 开始处理查询: {message[:50]}...")

        try:
            from app.core.llm import LLMServiceError, LLMTimeoutError
            from app.models.schemas import ListOrderedSection, OrderedListItem, TextSection, Section
            import json

            # 1. 生成 SQL 和执行查询
            logger.info(f"[SQL-1] 开始生成 SQL...")
            sql, chart_type = await self.generate_sql(message)
            logger.info(f"[SQL-1] 生成的 SQL: {sql[:80]}...")

            logger.info(f"[SQL-2] 开始执行查询...")
            result = await self.execute_query(sql, db)
            logger.info(f"[SQL-2完成] 查询返回 {len(result)} 条数据")

            # 2. 返回查询摘要
            if result:
                result_summary = f"查询到 {len(result)} 条数据"
                result_preview = result[:5]  # 前5条数据作为预览
            else:
                result_summary = "未查询到数据"
                result_preview = []

            logger.info(f"[SQL-3] 发送查询结果摘要")
            yield {
                "type": "sources",
                "sources": [{
                    "document_id": 0,
                    "title": "数据查询",
                    "filename": "database",
                    "chunk_index": 0,
                    "relevance": 1.0,
                    "relevance_percentage": "100%",
                    "text_preview": f"SQL: {sql[:100]}..."
                }],
                "confidence": 0.95,
            }

            # 3. 构建结构化 prompt，让 LLM 输出 JSON sections
            logger.info(f"[SQL-4] 构建结构化 prompt...")
            prompt = self._build_structured_query_prompt(message, sql, result_preview, result_summary)

            # 4. 流式调用 LLM，累积完整响应
            logger.info(f"[SQL-5] 开始调用 LLM 流式处理...")
            accumulated_content = ""
            try:
                async for chunk in self.llm.stream_text(prompt, max_tokens=2048):
                    accumulated_content += chunk
            except (LLMServiceError, LLMTimeoutError) as e:
                logger.error(f"[SQL-5错误] LLM 流式调用失败: {e}")
                yield {
                    "type": "error",
                    "message": f"LLM 服务错误：{str(e)}"
                }
                return

            logger.info(f"[SQL-5完成] LLM 流式处理完成，获得 {len(accumulated_content)} 字符的响应")

            # 5. 解析 LLM 输出为 Section 对象
            # 返回原始 LLM 响应（用于调试和日志）
            logger.info(f"[SQL-6] 返回原始 LLM 输出用于调试")
            yield {
                "type": "debug",
                "llm_output": accumulated_content
            }

            logger.info(f"[SQL-7] 开始解析 JSON 并生成 sections...")
            try:
                sections_data = json.loads(accumulated_content)
                if not isinstance(sections_data, list):
                    sections_data = [sections_data]
                logger.info(f"[SQL-7完成] 直接 JSON 解析成功，得到 {len(sections_data)} 个 sections")
            except json.JSONDecodeError:
                logger.warning("[SQL-7] LLM 返回的不是有效 JSON，尝试提取代码块中的 JSON")
                # 尝试从代码块中提取 JSON
                extracted_json = self._extract_json_from_codeblock(accumulated_content)
                if extracted_json:
                    try:
                        sections_data = json.loads(extracted_json)
                        if not isinstance(sections_data, list):
                            sections_data = [sections_data]
                        logger.info(f"[SQL-7完成] 代码块 JSON 解析成功，得到 {len(sections_data)} 个 sections")
                    except json.JSONDecodeError:
                        logger.warning("[SQL-7] 代码块中的 JSON 解析失败，使用降级处理")
                        sections_data = self._parse_markdown_to_sections(accumulated_content)
                        logger.info(f"[SQL-7完成] Markdown 降级处理，得到 {len(sections_data)} 个 sections")
                else:
                    logger.warning("[SQL-7] 未找到代码块，使用降级处理")
                    sections_data = self._parse_markdown_to_sections(accumulated_content)
                    logger.info(f"[SQL-7完成] Markdown 降级处理，得到 {len(sections_data)} 个 sections")

            # 6. 逐块返回 section
            logger.info(f"[SQL-8] 开始返回 {len(sections_data)} 个 sections...")
            for idx, section_data in enumerate(sections_data):
                try:
                    section = self._validate_section(section_data)
                    logger.debug(f"[SQL-8] 返回 section {idx+1}/{len(sections_data)}: {section.type}")
                    yield {
                        "type": "section",
                        "section": section.model_dump()
                    }
                except ValueError as e:
                    logger.warning(f"[SQL-8] Invalid section data at index {idx}: {e}, skipping")
                    continue

            # 7. 完成事件
            logger.info(f"[SQL完成] 流式处理完毕")
            yield {
                "type": "done",
                "confidence": 0.95,
            }

        except Exception as e:
            logger.error(f"[SQL错误] stream_with_structure 失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": f"处理失败：{str(e)}"
            }

    def _build_structured_query_prompt(
        self, message: str, sql: str, result_preview: list, result_summary: str
    ) -> str:
        """构建结构化查询 prompt"""
        prompt = f"""用户查询：{message}

执行的SQL：{sql}

查询结果摘要：{result_summary}

数据预览（前5条）：
{json.dumps(result_preview, ensure_ascii=False, indent=2)}

请将查询结果转换为以下 JSON 格式的 sections 数组，每个 section 是一个信息块：

[
  {{
    "type": "text",
    "markdown": "查询结果分析文本"
  }},
  {{
    "type": "list_ordered",
    "items": [
      {{
        "title": "第一条数据摘要",
        "details_markdown": "详细信息"
      }}
    ]
  }}
]

要求：
1. 直接返回 JSON 数组，不要有任何其他文字
2. 如果结果是表格数据，用 list_ordered 展示关键行
3. markdown 字段可以用 **粗体** 和其他 markdown 语法
4. 不要显示完整的原始 JSON 数据
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

        # 按 ## 标题分段
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

    def _extract_json_from_codeblock(self, content: str) -> Optional[str]:
        """从 markdown 代码块中提取 JSON"""
        import re
        # 匹配 ```json ... ``` 或 ``` ... ```
        pattern = r'```(?:json)?\s*\n([\s\S]*?)\n```'
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
        return None


sql_service = SQLService()
