"""
RAG 模型微调评估方法
使用 RAGAS 框架评估检索增强生成质量
"""

import json
import asyncio
from typing import List, Dict
from app.services.rag_service import RAGService
from app.core.llm import llm_client


class RAGEvaluator:
    """RAG 评估工具"""

    def __init__(self):
        self.rag = RAGService()

    async def evaluate_single_query(
        self,
        question: str,
        ground_truth: str,
        retrieved_docs: List[str],
        generated_answer: str
    ) -> Dict[str, float]:
        """评估单个问答的四大指标"""

        metrics = {}

        # 1. Faithfulness（忠实度）- 答案是否基于检索文档
        faithfulness_prompt = f"""
请判断以下答案是否忠实于提供的文档内容。

文档内容：
{chr(10).join(retrieved_docs)}

答案：{generated_answer}

评分标准：
- 1.0：所有陈述都能在文档中找到依据
- 0.5：部分陈述有依据，部分为推断
- 0.0：包含明显与文档矛盾或无依据的内容

输出：仅输出分数（0.0-1.0）
"""

        faithfulness = await llm_client.generate_text(faithfulness_prompt)
        metrics["faithfulness"] = float(faithfulness.strip())

        # 2. Answer Relevance（答案相关性） - 答案是否回答了问题
        relevance_prompt = f"""
请判断以下答案与问题的相关性。

问题：{question}
答案：{generated_answer}

评分标准：
- 1.0：完整回答了问题核心
- 0.5：部分回答或过于笼统
- 0.0：完全无关或未回答

输出：仅输出分数（0.0-1.0）
"""

        relevance = await llm_client.generate_text(relevance_prompt)
        metrics["answer_relevance"] = float(relevance.strip())

        # 3. Context Relevance（上下文相关性） - 检索文档是否与问题相关
        context_relevance = sum(
            1 for doc in retrieved_docs
            if any(keyword in doc.lower() for keyword in question.lower().split())
        ) / len(retrieved_docs)
        metrics["context_relevance"] = min(context_relevance, 1.0)

        # 4. Context Precision（上下文精确度） - 检索排序是否准确
        precision_prompt = f"""
请评估检索文档的排序质量。

问题：{question}
检索文档（已排序）：
{chr(10).join([f"{i+1}. {doc[:100]}..." for i, doc in enumerate(retrieved_docs)])}

评分标准：
- 1.0：最相关的文档排在最前
- 0.5：相关文档位置中等
- 0.0：排序完全不合理

输出：仅输出分数（0.0-1.0）
"""

        precision = await llm_client.generate_text(precision_prompt)
        metrics["context_precision"] = float(precision.strip())

        return metrics

    async def compare_models(
        self,
        test_dataset: List[Dict],
        baseline_model: str,
        finetuned_model: str
    ) -> Dict:
        """对比基线模型和微调模型"""

        results = {
            "baseline": {"faithfulness": [], "answer_relevance": [], "context_relevance": []},
            "finetuned": {"faithfulness": [], "answer_relevance": [], "context_relevance": []}
        }

        for sample in test_dataset:
            # TODO: 切换不同模型进行评估
            baseline_metrics = await self.evaluate_single_query(
                sample["question"],
                sample["ground_truth"],
                sample["retrieved_docs"],
                sample["baseline_answer"]
            )

            finetuned_metrics = await self.evaluate_single_query(
                sample["question"],
                sample["ground_truth"],
                sample["retrieved_docs"],
                sample["finetuned_answer"]
            )

            for metric, value in baseline_metrics.items():
                results["baseline"][metric].append(value)
                results["finetuned"][metric].append(finetuned_metrics[metric])

        # 计算平均值
        summary = {}
        for model in ["baseline", "finetuned"]:
            summary[model] = {
                metric: sum(values) / len(values)
                for metric, values in results[model].items()
            }

        return summary

    def generate_report(self, comparison: Dict) -> str:
        """生成评估报告"""

        report = """
# RAG 模型微调评估报告

## 基线模型 vs 微调模型

| 指标 | 基线模型 | 微调模型 | 提升 |
|------|---------|---------|------|
"""

        for metric in ["faithfulness", "answer_relevance", "context_relevance", "context_precision"]:
            baseline = comparison["baseline"][metric]
            finetuned = comparison["finetuned"][metric]
            improvement = ((finetuned - baseline) / baseline) * 100 if baseline > 0 else 0

            report += f"| {metric} | {baseline:.2f} | {finetuned:.2f} | +{improvement:.1f}% |\n"

        report += "\n## 结论\n\n"

        avg_improvement = sum(
            ((comparison["finetuned"][m] - comparison["baseline"][m]) / comparison["baseline"][m])
            for m in comparison["baseline"].keys()
        ) / len(comparison["baseline"]) * 100

        if avg_improvement > 10:
            report += f"✅ 微调效果显著（平均提升 {avg_improvement:.1f}%），建议部署使用。\n"
        elif avg_improvement > 5:
            report += f"⚠️ 微调效果一般（平均提升 {avg_improvement:.1f}%），建议优化数据集。\n"
        else:
            report += f"❌ 微调效果不明显（平均提升 {avg_improvement:.1f}%），建议重新设计训练数据。\n"

        return report


# RAGAS 官方库使用（推荐）
def use_ragas_library():
    """使用 RAGAS 官方评估库"""

    # 安装
    # pip install ragas

    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevance, context_relevance

    # 评估数据集格式
    dataset = [
        {
            "question": "...",
            "answer": "...",
            "contexts": ["doc1", "doc2"],  # 检索文档
            "ground_truth": "..."  # 标准答案
        }
    ]

    # 自动评估
    results = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevance, context_relevance]
    )

    # 输出分数
    print(results)


if __name__ == "__main__":
    # 示例评估数据
    test_data = [
        {
            "question": "退货政策是什么？",
            "ground_truth": "7天内无理由退货",
            "retrieved_docs": ["文档1：退货政策规定...", "文档2：售后服务说明..."],
            "baseline_answer": "可以退货",  # 基线模型回答
            "finetuned_answer": "根据《售后服务管理办法》第3条，商品购买后7天内可无理由退货..."  # 微调模型回答
        }
    ]

    evaluator = RAGEvaluator()

    # 异步评估
    asyncio.run(evaluator.compare_models(test_data, "baseline", "finetuned"))