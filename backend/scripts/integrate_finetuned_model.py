"""
微调模型集成到 AIGovern Pro 系统
将微调后的 RAG 模型替换原有 LLM 服务
"""

from typing import Optional, List, Dict
from app.core.llm import llm_client


class FineTunedRAGService:
    """使用微调模型的 RAG 服务"""

    def __init__(self, finetuned_model_name: str):
        """
        Args:
            finetuned_model_name: 微调模型名称（云端平台返回）
        """
        self.model_name = finetuned_model_name
        self.llm = llm_client  # 原有 LLM 客户端

    async def generate_answer_with_finetuned(
        self,
        question: str,
        retrieved_docs: List[Dict]
    ) -> str:
        """使用微调模型生成答案"""

        # 构建上下文
        context = "\n\n".join(
            [f"文档 {i+1}: {doc['text']}" for i, doc in enumerate(retrieved_docs)]
        )

        # 调用微调模型（需要修改 llm_client 支持模型切换）
        prompt = f"""请基于以下文档回答问题。

文档内容：
{context}

问题：{question}

要求：
1. 准确引用文档内容
2. 标注引用来源
3. 简洁清晰
"""

        # TODO: 切换到微调模型
        # 方案1：云端 API 调用（阿里云百炼）
        if "bailian://" in self.model_name:
            answer = await self._call_bailian_model(self.model_name, prompt)

        # 方案2：ModelScope 模型
        elif "modelscope://" in self.model_name:
            answer = await self._call_modelscope_model(self.model_name, prompt)

        # 方案3：本地部署模型
        else:
            answer = await self._call_local_model(self.model_name, prompt)

        return answer

    async def _call_bailian_model(self, model_name: str, prompt: str) -> str:
        """调用阿里云百炼微调模型"""
        # TODO: 实现百炼 API 调用
        # 文档：https://help.aliyun.com/document_detail/2712520.html
        pass

    async def _call_modelscope_model(self, model_name: str, prompt: str) -> str:
        """调用 ModelScope 微调模型"""
        # TODO: 实现 ModelScope API 调用
        pass

    async def _call_local_model(self, model_path: str, prompt: str) -> str:
        """调用本地部署的微调模型"""

        from transformers import AutoModelForCausalLM, AutoTokenizer

        # 加载模型（首次加载较慢）
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            trust_remote_code=True
        )

        # 生成答案
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=512)
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return answer


# 修改原有 rag_service.py 的集成方案
"""
# backend/app/services/rag_service.py

from app.core.config import settings

class RAGService:
    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session
        # 根据配置选择模型
        if settings.USE_FINETUNED_MODEL:
            self.llm = FineTunedRAGService(settings.FINETUNED_MODEL_NAME)
        else:
            self.llm = llm_client
"""


# 配置文件修改
"""
# backend/app/core/config.py

class Settings:
    # 微调模型配置
    USE_FINETUNED_MODEL: bool = False  # 是否使用微调模型
    FINETUNED_MODEL_NAME: str = ""  # 微调模型名称

    # 模型调用方式
    MODEL_DEPLOYMENT_TYPE: str = "api"  # api | local | hybrid

    # API 模式配置
    BAILIAN_API_KEY: str = ""
    MODELSCOPE_API_KEY: str = ""

    # 本地模式配置
    LOCAL_MODEL_PATH: str = "./models/aigovern-rag-v1"
"""


# 渐进式上线策略
class ABTestRAGService:
    """A/B 测试：同时运行基线和微调模型"""

    def __init__(self):
        self.baseline_llm = llm_client
        self.finetuned_llm = FineTunedRAGService("your-model-name")
        self.traffic_split = 0.2  # 20% 流量使用微调模型

    async def generate_answer_ab_test(
        self,
        question: str,
        retrieved_docs: List[Dict],
        user_id: str
    ) -> tuple[str, str]:
        """
        A/B 测试生成答案
        返回：(答案, 模型标识)
        """

        import random

        # 根据用户 ID 哈希分流（确保同一用户始终使用同一模型）
        if hash(user_id) % 100 < self.traffic_split * 100:
            # 使用微调模型
            answer = await self.finetuned_llm.generate_answer_with_finetuned(
                question, retrieved_docs
            )
            model_flag = "finetuned"
        else:
            # 使用基线模型
            answer = await self.baseline_llm.generate_text(question)
            model_flag = "baseline"

        return answer, model_flag


if __name__ == "__main__":
    # 集成测试
    test_question = "退货政策是什么？"
    test_docs = [{"text": "文档内容..."}]

    service = FineTunedRAGService("bailian://aigovern-rag-v1")
    answer = service.generate_answer_with_finetuned(test_question, test_docs)

    print(f"微调模型回答：{answer}")