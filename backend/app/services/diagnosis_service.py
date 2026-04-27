from typing import Optional, AsyncIterator, Any
from app.core.llm import llm_client
from app.models.schemas import (
    TextSection,
    ListUnorderedSection,
    ListOrderedSection,
    OrderedListItem,
    StructuredChatResponse,
)
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class DiagnosisService:
    """经营诊断服务 - OLAP 数据分析"""

    def __init__(self):
        self.llm = llm_client

    async def analyze_metrics(self, metrics: dict[str, float]) -> dict:
        """分析关键指标，识别异常"""

        issues = []

        # 简单规则检测
        if metrics.get("order_count", 0) < 500:
            issues.append({
                "issue": "订单数下降",
                "severity": "high",
                "current": metrics.get("order_count"),
                "threshold": 500,
            })

        if metrics.get("conversion_rate", 0) < 2.0:
            issues.append({
                "issue": "转化率偏低",
                "severity": "medium",
                "current": metrics.get("conversion_rate"),
                "threshold": 2.0,
            })

        if metrics.get("active_users", 0) < 3000:
            issues.append({
                "issue": "活跃用户数下降",
                "severity": "high",
                "current": metrics.get("active_users"),
                "threshold": 3000,
            })

        return {
            "total_issues": len(issues),
            "issues": issues,
            "metrics": metrics,
        }

    async def root_cause_analysis(self, issue: str, context: dict) -> str:
        """根因分析"""

        prompt = f"""作为一个数据分析专家，分析以下经营问题的根本原因。

问题：{issue}

背景数据：
{context}

请提供：
1. 问题的根本原因
2. 影响范围
3. 应采取的措施

使用简洁的中文说明。
"""

        analysis = await self.llm.generate_text(prompt, max_tokens=512)
        return analysis

    async def generate_recommendation(self, analysis: str) -> str:
        """生成决策建议"""

        prompt = f"""基于以下分析，为企业提供可行的改进建议。

分析结果：
{analysis}

要求：
1. 提供 3-5 个具体的改进建议
2. 每个建议说明优先级和预期效果
3. 建议要可落地执行

使用中文说明。
"""

        recommendations = await self.llm.generate_text(prompt, max_tokens=1024)
        return recommendations

    async def generate_diagnosis_report(
        self, metrics: dict[str, float], time_period: str = "最近 7 天"
    ) -> dict:
        """生成完整诊断报告"""

        # 1. 分析指标
        analysis_result = await self.analyze_metrics(metrics)

        # 2. 根因分析
        root_causes = {}
        for issue in analysis_result["issues"]:
            cause = await self.root_cause_analysis(issue["issue"], metrics)
            root_causes[issue["issue"]] = cause

        # 3. 建议生成
        recommendations = await self.generate_recommendation(str(root_causes))

        return {
            "period": time_period,
            "metrics": metrics,
            "analysis": analysis_result,
            "root_causes": root_causes,
            "recommendations": recommendations,
        }

    async def stream_with_structure(
        self, message: str, metrics: dict, db = None
    ) -> AsyncIterator[dict]:
        """结构化流式处理诊断结果"""
        logger.info(f"[Diagnosis流式处理] 开始处理查询: {message[:50]}...")

        try:
            from app.core.llm import LLMServiceError, LLMTimeoutError

            # 1. 计算指标
            logger.info(f"[Diagnosis-1] 开始分析指标...")
            analysis = await self.analyze_metrics(metrics)
            logger.info(f"[Diagnosis-1完成] 发现 {analysis['total_issues']} 个问题")

            # 2. 返回诊断摘要
            logger.info(f"[Diagnosis-2] 发送诊断摘要")
            yield {
                "type": "sources",
                "sources": [{
                    "document_id": 0,
                    "title": "经营诊断",
                    "filename": "diagnosis",
                    "chunk_index": 0,
                    "relevance": 1.0,
                    "relevance_percentage": "100%",
                    "text_preview": f"问题数: {analysis['total_issues']}"
                }],
                "confidence": 0.92,
            }

            # 3. 构建结构化 prompt
            logger.info(f"[Diagnosis-3] 构建结构化 prompt...")
            prompt = self._build_structured_diagnosis_prompt(message, metrics, analysis)

            # 4. 流式调用 LLM，累积完整响应
            logger.info(f"[Diagnosis-4] 开始调用 LLM 流式处理...")
            accumulated_content = ""
            try:
                async for chunk in self.llm.stream_text(prompt, max_tokens=2048):
                    accumulated_content += chunk
            except (LLMServiceError, LLMTimeoutError) as e:
                logger.error(f"[Diagnosis-4错误] LLM 流式调用失败: {e}")
                yield {
                    "type": "error",
                    "message": f"LLM 服务错误：{str(e)}"
                }
                return

            logger.info(f"[Diagnosis-4完成] LLM 流式处理完成，获得 {len(accumulated_content)} 字符的响应")

            # 5. 解析 LLM 输出为 Section 对象
            # 返回原始 LLM 响应（用于调试和日志）
            logger.info(f"[Diagnosis-5] 返回原始 LLM 输出用于调试")
            yield {
                "type": "debug",
                "llm_output": accumulated_content
            }

            logger.info(f"[Diagnosis-6] 开始解析 JSON 并生成 sections...")
            try:
                sections_data = json.loads(accumulated_content)
                if not isinstance(sections_data, list):
                    sections_data = [sections_data]
                logger.info(f"[Diagnosis-6完成] 直接 JSON 解析成功，得到 {len(sections_data)} 个 sections")
            except json.JSONDecodeError:
                logger.warning("[Diagnosis-6] LLM 返回的不是有效 JSON，尝试提取代码块中的 JSON")
                extracted_json = self._extract_json_from_codeblock(accumulated_content)
                if extracted_json:
                    try:
                        sections_data = json.loads(extracted_json)
                        if not isinstance(sections_data, list):
                            sections_data = [sections_data]
                        logger.info(f"[Diagnosis-6完成] 代码块 JSON 解析成功，得到 {len(sections_data)} 个 sections")
                    except json.JSONDecodeError:
                        logger.warning("[Diagnosis-6] 代码块中的 JSON 解析失败，使用降级处理")
                        sections_data = self._parse_markdown_to_sections(accumulated_content)
                        logger.info(f"[Diagnosis-6完成] Markdown 降级处理，得到 {len(sections_data)} 个 sections")
                else:
                    logger.warning("[Diagnosis-6] 未找到代码块，使用降级处理")
                    sections_data = self._parse_markdown_to_sections(accumulated_content)
                    logger.info(f"[Diagnosis-6完成] Markdown 降级处理，得到 {len(sections_data)} 个 sections")

            # 6. 逐块返回 section
            logger.info(f"[Diagnosis-7] 开始返回 {len(sections_data)} 个 sections...")
            for idx, section_data in enumerate(sections_data):
                try:
                    section = self._validate_section(section_data)
                    logger.debug(f"[Diagnosis-7] 返回 section {idx+1}/{len(sections_data)}: {section.type}")
                    yield {
                        "type": "section",
                        "section": section.model_dump()
                    }
                except ValueError as e:
                    logger.warning(f"[Diagnosis-7] Invalid section data at index {idx}: {e}, skipping")
                    continue

            # 7. 完成事件
            logger.info(f"[Diagnosis完成] 流式处理完毕")
            yield {
                "type": "done",
                "confidence": 0.92,
            }

        except Exception as e:
            logger.error(f"[Diagnosis错误] stream_with_structure 失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": f"处理失败：{str(e)}"
            }

    def _build_structured_diagnosis_prompt(self, message: str, metrics: dict, analysis: dict) -> str:
        """构建结构化诊断 prompt"""
        prompt = f"""用户查询：{message}

关键指标：
{json.dumps(metrics, ensure_ascii=False, indent=2)}

诊断分析：
{json.dumps(analysis, ensure_ascii=False, indent=2)}

请将诊断结果转换为以下 JSON 格式的 sections 数组：

[
  {{
    "type": "text",
    "markdown": "经营状况总体评价"
  }},
  {{
    "type": "list_ordered",
    "items": [
      {{
        "title": "问题1",
        "details_markdown": "影响和建议"
      }}
    ]
  }}
]

要求：
1. 直接返回 JSON 数组，不要有任何其他文字
2. 如果存在问题，用 🔴 标记高严重性问题，🟡 标记中等严重性问题
3. 用 list_ordered 展示各个问题及其影响
4. 用 text section 提供整体评价和改进方向
5. 确保返回的 JSON 格式正确
"""
        return prompt

    def _validate_section(self, data: dict) -> TextSection:
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

    def _extract_json_from_codeblock(self, content: str):
        """从 markdown 代码块中提取 JSON"""
        import re
        pattern = r'```(?:json)?\s*\n([\s\S]*?)\n```'
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
        return None


diagnosis_service = DiagnosisService()

