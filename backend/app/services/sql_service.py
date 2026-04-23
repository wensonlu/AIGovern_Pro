from typing import Optional, Any
from app.core.llm import llm_client
from sqlalchemy import text
from sqlalchemy.orm import Session


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


sql_service = SQLService()
