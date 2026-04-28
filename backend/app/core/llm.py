import httpx
import json
from typing import AsyncIterator, Optional
from app.core.config import settings
import hashlib
from dashscope import TextEmbedding


class LLMServiceError(RuntimeError):
    """LLM 服务调用失败"""


class LLMTimeoutError(LLMServiceError):
    """LLM 服务响应超时"""


class LLMClient:
    """LLM 客户端 - 支持豆包和通义千问"""

    def __init__(self):
        self.api_key = settings.llm_api_key
        self.model_name = settings.llm_model_name
        self.provider = settings.llm_provider
        self.api_base = settings.llm_api_base
        self.anthropic_base_url = settings.anthropic_base_url.rstrip("/")
        self.anthropic_auth_token = settings.anthropic_auth_token

        # Embedding 单独配置
        self.embedding_api_key = settings.embedding_api_key
        self.embedding_model_name = settings.embedding_model_name
        self.embedding_provider = settings.embedding_provider
        self.embedding_api_base = settings.embedding_api_base

    async def generate_text(self, prompt: str, max_tokens: int = 2048) -> str:
        """生成文本回复"""
        if not self.api_key:
            raise ValueError("LLM API Key 未配置，请在 .env 文件中设置 LLM_API_KEY")

        try:
            if self.provider == "doubao":
                return await self._generate_with_doubao(prompt, max_tokens)
            elif self.provider == "qwen":
                return await self._generate_with_qwen(prompt, max_tokens)
            elif self.provider == "anthropic":
                return await self._generate_with_anthropic(prompt, max_tokens)
            else:
                raise ValueError(f"不支持的 LLM 提供者: {self.provider}")
        except httpx.TimeoutException as e:
            raise LLMTimeoutError("LLM 服务响应超时，请稍后重试") from e
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            raise LLMServiceError(f"LLM 服务返回异常状态码: {status_code}") from e
        except httpx.RequestError as e:
            raise LLMServiceError(f"LLM 服务请求失败: {e}") from e

    async def stream_text(
        self, prompt: str, max_tokens: int = 2048
    ) -> AsyncIterator[str]:
        """流式生成文本回复"""
        if not self.api_key:
            raise ValueError("LLM API Key 未配置，请在 .env 文件中设置 LLM_API_KEY")

        try:
            if self.provider == "doubao":
                async for chunk in self._stream_with_doubao(prompt, max_tokens):
                    yield chunk
            else:
                text = await self.generate_text(prompt, max_tokens)
                for index in range(0, len(text), 8):
                    yield text[index:index + 8]
        except httpx.TimeoutException as e:
            raise LLMTimeoutError("LLM 服务响应超时，请稍后重试") from e
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            raise LLMServiceError(f"LLM 服务返回异常状态码: {status_code}") from e
        except httpx.RequestError as e:
            raise LLMServiceError(f"LLM 服务请求失败: {e}") from e

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

    async def _stream_with_doubao(
        self, prompt: str, max_tokens: int
    ) -> AsyncIterator[str]:
        """豆包 OpenAI 兼容接口流式调用"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue

                    payload_text = line.removeprefix("data:").strip()
                    if payload_text == "[DONE]":
                        break

                    data = json.loads(payload_text)
                    choices = data.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content

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

    async def _generate_with_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Anthropic Messages API 调用（兼容 ADA 网关）"""
        if not self.anthropic_auth_token:
            raise ValueError("Anthropic Auth Token 未配置，请在 .env 文件中设置 ANTHROPIC_AUTH_TOKEN")

        headers = {
            "Authorization": f"Bearer {self.anthropic_auth_token}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.anthropic_base_url}/v1/messages",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("content", [])
            text_parts = [
                block["text"]
                for block in content
                if isinstance(block, dict) and isinstance(block.get("text"), str)
            ]
            if text_parts:
                return "".join(text_parts)
            raise ValueError(f"无法解析 Anthropic 响应: {data}")

    async def generate_embedding(self, text: str) -> list[float]:
        """生成文本嵌入向量（768维）"""
        if not self.embedding_api_key:
            raise ValueError("Embedding API Key 未配置，请在 .env 文件中设置 EMBEDDING_API_KEY")

        try:
            if self.embedding_provider == "doubao":
                return await self._generate_embedding_doubao(text)
            elif self.embedding_provider == "qwen":
                # 通义千问SDK是同步的，用线程池异步执行
                import asyncio
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self._generate_embedding_qwen_sync, text)
            else:
                raise ValueError(f"不支持的 Embedding 提供者: {self.embedding_provider}")
        except Exception as e:
            # 嵌入向量 API 失败 - 降级到 mock 实现
            print(f"⚠️  嵌入向量 API 调用失败: {e}")
            print(f"⚠️  使用本地 mock 实现作为临时方案")
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
            "Authorization": f"Bearer {self.embedding_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.embedding_model_name,
            "input": {
                "texts": [text]
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.embedding_api_base,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            # 豆包 embedding 返回格式：{"data": [{"embedding": [...]}]}
            embeddings = data.get("data", [])
            if embeddings:
                return embeddings[0]["embedding"]
            raise ValueError(f"无法解析豆包 embedding 响应: {data}")

    def _generate_embedding_qwen_sync(self, text: str) -> list[float]:
        """通义千问嵌入向量 API（同步版）"""
        response = TextEmbedding.call(
            model=self.embedding_model_name,
            input=text,
            api_key=self.embedding_api_key
        )

        if response.status_code == 200:
            embeddings = response.output.get('embeddings', [])
            if embeddings:
                return embeddings[0]['embedding']
            raise ValueError(f"无法从响应中提取 embedding: {response.output}")
        else:
            raise ValueError(f"API返回非200状态: {response.status_code} - {response.message}")

    async def _generate_embedding_qwen(self, text: str) -> list[float]:
        """通义千问嵌入向量 API（异步版 - 已废弃，改用同步版）"""
        raise NotImplementedError("使用 _generate_embedding_qwen_sync 代替")


llm_client = LLMClient()
