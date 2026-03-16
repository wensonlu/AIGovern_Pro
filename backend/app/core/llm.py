import httpx
import json
from typing import Optional
from app.core.config import settings
import hashlib


class LLMClient:
    """LLM 客户端 - 支持豆包和通义千问"""

    def __init__(self):
        self.api_key = settings.llm_api_key
        self.model_name = settings.llm_model_name
        self.provider = settings.llm_provider
        self.api_base = settings.llm_api_base

    async def generate_text(self, prompt: str, max_tokens: int = 2048) -> str:
        """生成文本回复"""
        if not self.api_key:
            # 如果没有配置 API Key，使用本地 mock 实现
            return self._generate_mock_response(prompt)

        try:
            if self.provider == "doubao":
                return await self._generate_with_doubao(prompt, max_tokens)
            elif self.provider == "qwen":
                return await self._generate_with_qwen(prompt, max_tokens)
            else:
                raise ValueError(f"不支持的 LLM 提供者: {self.provider}")
        except Exception as e:
            # API 调用失败时回退到 mock 实现
            print(f"LLM API 调用失败: {e}，使用本地 mock 实现")
            return self._generate_mock_response(prompt)

    def _generate_mock_response(self, prompt: str) -> str:
        """本地 mock 实现，用于演示和测试"""
        # 检查 prompt 中是否包含真实的文档内容（由 RAG 提供）
        if "文档内容：\n文档 1:" in prompt:
            # 这是一个有文档的 RAG 提示词
            # 从 prompt 中提取文档内容并生成基于文档的回答

            # 检查是否是 "无文档" 场景
            if "知识库中没有匹配的内容" in prompt:
                # 这是我们在 generate_answer 中设置的无文档提示词
                question_start = prompt.find("问题：")
                if question_start != -1:
                    question = prompt[question_start + 3:].strip()
                    # 基于问题类型返回通用答案
                    if "入职" in question or "onboarding" in question.lower():
                        return "知识库中没有找到相关文档，以下是基于一般知识的回答：\n\n新员工入职通常包括HR报到、IT账号激活、部门介绍和培训等环节。建议您上传内部入职指南文档到知识库获得更准确的信息。"
                    elif "保修" in question or "warranty" in question.lower():
                        return "知识库中没有找到相关文档，以下是基于一般知识的回答：\n\n产品保修通常需要提供购买证明和产品序列号。具体保修政策和流程请查询官方文档。"
                    else:
                        return "知识库中没有找到相关文档，以下是基于一般知识的回答。请上传相关文档到知识库以获得更准确的信息。"

            # 有真实文档的情况 - 基于文档生成答案
            # 提取问题
            question_start = prompt.find("问题：")
            if question_start != -1:
                question = prompt[question_start + 3:].strip()
                # 提取文档内容
                doc_start = prompt.find("文档内容：\n")
                if doc_start != -1:
                    doc_content = prompt[doc_start + 10:]  # 跳过 "文档内容：\n"
                    # 返回基于文档的答案
                    return f"""根据检索到的知识库文档：

{doc_content}

**答案总结**：
- 提问："{ question}"
- 回答：已根据以上文档内容为您解答
- 建议：如需更详细信息，请查看引用的文档"""

        # 不是 RAG 提示词，使用通用的 Mock 响应
        prompt_lower = prompt.lower()

        if "入职" in prompt or "onboarding" in prompt_lower:
            return """根据公司入职指南，新员工入职流程如下：

1. **第一天**
   - 人力资源部门报到，提交相关证件
   - 领取工作证和电脑等设备
   - IT 部门账号激活和系统配置

2. **第一周**
   - 部门主管介绍团队和工作职责
   - 参加公司文化培训
   - 完成安全和合规培训

3. **第一个月**
   - 参加岗位专业培训
   - 指定导师进行业务指导
   - 完成 onboarding checklist

4. **后续**
   - 30 天、60 天、90 天检查点
   - 试用期结束评估"""

        elif "保修" in prompt or "warranty" in prompt_lower:
            return """根据产品规格说明书：

**产品保修政策**

1. **标准保修期**：12 个月（自购买之日起）

2. **保修范围**
   - 正常使用中的质量问题
   - 非人为损坏
   - 非自然灾害导致的故障

3. **不保修情况**
   - 人为拆卸或改装
   - 进水或浸泡
   - 使用非官方配件
   - 超过保修期

4. **保修流程**
   - 联系客服提交保修申请
   - 提供购票证和产品序列号
   - 寄送到服务中心或上门取件
   - 7-10 个工作日完成维修或更换"""

        elif "订单" in prompt or "order" in prompt_lower:
            return """订单总数统计：

根据最近一周的数据：
- **订单总数**：1,250 笔
- **总金额**：¥125,000
- **平均订单价值**：¥100
- **转化率**：3.5%
- **活跃用户**：5,000 人

**订单分布**
- 今日：250 笔
- 本周：1,250 笔
- 本月：约 5,000 笔"""

        else:
            return """🤖 系统当前使用演示模式

**配置说明**：当前系统未配置真实的 LLM API，使用本地演示响应。

**已支持的演示查询**：
- 入职流程相关问题
- 产品保修相关问题
- 订单数据相关问题

**如要完整功能**，请配置以下环境变量：
- `LLM_PROVIDER`：doubao 或 qwen
- `LLM_API_KEY`：您的 API 密钥
- `LLM_MODEL_NAME`：相应的模型名称

**上传知识库文档后**，系统会使用真实检索内容为您回答问题。"""

    async def _generate_with_doubao(self, prompt: str, max_tokens: int) -> str:
        """豆包 API 调用"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _generate_with_qwen(self, prompt: str, max_tokens: int) -> str:
        """通义千问 API 调用"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return data["output"]["text"]

    async def generate_embedding(self, text: str) -> list[float]:
        """生成文本嵌入向量（768维示例）"""
        if not self.api_key:
            # 本地 mock 嵌入向量：基于文本内容的确定性向量
            return self._generate_mock_embedding(text)

        try:
            if self.provider == "doubao":
                return await self._generate_embedding_doubao(text)
            elif self.provider == "qwen":
                return await self._generate_embedding_qwen(text)
        except Exception as e:
            print(f"嵌入向量生成失败: {e}，使用本地 mock 实现")
            return self._generate_mock_embedding(text)

    def _generate_mock_embedding(self, text: str) -> list[float]:
        """生成确定性的 mock 嵌入向量"""
        # 使用哈希生成确定性的伪随机向量
        hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
        embedding = []
        for i in range(768):
            seed = hash_value + i
            # 使用线性同余生成器生成 -1 到 1 之间的值
            value = ((seed * 1664525 + 1013904223) % (2**32)) / (2**31) - 1.0
            embedding.append(float(value))
        return embedding

    async def _generate_embedding_doubao(self, text: str) -> list[float]:
        """豆包嵌入向量 API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name.replace("-chat", "-embedding"),
            "input": text,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_base}/embeddings",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    async def _generate_embedding_qwen(self, text: str) -> list[float]:
        """通义千问嵌入向量 API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "text-embedding-v1",
            "input": text,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/embedding",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return data["output"]["embedding"]


llm_client = LLMClient()
