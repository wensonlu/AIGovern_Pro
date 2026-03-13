import httpx
from typing import Optional
from app.core.config import settings


class LLMClient:
    """LLM 客户端 - 支持豆包和通义千问"""

    def __init__(self):
        self.api_key = settings.llm_api_key
        self.model_name = settings.llm_model_name
        self.provider = settings.llm_provider
        self.api_base = settings.llm_api_base

    async def generate_text(self, prompt: str, max_tokens: int = 2048) -> str:
        """生成文本回复"""
        if self.provider == "doubao":
            return await self._generate_with_doubao(prompt, max_tokens)
        elif self.provider == "qwen":
            return await self._generate_with_qwen(prompt, max_tokens)
        else:
            raise ValueError(f"不支持的 LLM 提供者: {self.provider}")

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
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPError as e:
                raise RuntimeError(f"豆包 API 调用失败: {e}")

    async def _generate_with_qwen(self, prompt: str, max_tokens: int) -> str:
        """通义千问 API 调用（占位符实现）"""
        raise NotImplementedError("通义千问集成待实现")

    async def generate_embedding(self, text: str) -> list[float]:
        """生成文本嵌入向量"""
        # 占位符实现 - 实际应使用嵌入模型
        raise NotImplementedError("嵌入向量生成待实现")


llm_client = LLMClient()
