#!/usr/bin/env python
"""
阿里云百炼微调配置工具
文档：https://help.aliyun.com/document_detail/2712215.html
"""

import json
from datetime import datetime


class BailianFineTuner:
    """阿里云百炼微调工具"""

    def __init__(self):
        # TODO: 配置 API Key 和 OSS bucket
        self.api_key = "YOUR_BAILIAN_API_KEY"
        self.oss_bucket = "your-bucket-name"

    def prepare_config(self, train_file: str, val_file: str) -> dict:
        """生成微调配置"""

        config = {
            "model_type": "qwen-7b-chat",  # 推荐基础模型
            "hyperparameters": {
                # 关键参数（深入掌握的核心）
                "learning_rate": 5e-5,  # 学习率（影响收敛速度）
                "num_train_epochs": 3,  # 训练轮数
                "per_device_train_batch_size": 4,  # 批大小
                "gradient_accumulation_steps": 8,  # 梯度累积（模拟大 batch）

                # LoRA 特定参数
                "lora_rank": 16,  # LoRA 矩阵秩（8-64，越大模型能力越强）
                "lora_alpha": 32,  # LoRA 缩放系数
                "lora_dropout": 0.1,  # 防止过拟合

                # 优化参数
                "warmup_steps": 100,  # 预热步数
                "weight_decay": 0.01,  # 权重衰减
                "max_grad_norm": 1.0,  # 梯度裁剪
            },
            "training_data": {
                "train_file": train_file,
                "validation_file": val_file,
                "format": "alpaca",  # Alpaca 格式
            },
            "output": {
                "model_name": f"aigovern-rag-{datetime.now().strftime('%Y%m%d')}",
                "description": "AIGovern Pro RAG问答优化模型",
            }
        }

        return config

    def explain_parameters(self) -> dict:
        """参数详解（深入掌握必备）"""

        return {
            "learning_rate": {
                "default": "5e-5",
                "range": "1e-6 到 1e-4",
                "impact": "太大→训练不稳定，太小→收敛慢",
                "rule": "数据量大用小 LR，数据量小用大 LR",
            },
            "lora_rank": {
                "default": "16",
                "range": "8, 16, 32, 64",
                "impact": "秩越高，模型保留更多原有能力，但训练参数增加",
                "rule": "RAG 任务推荐 16-32（平衡性能与成本）",
            },
            "num_train_epochs": {
                "default": "3",
                "rule": "数据集小→多轮训练，数据集大→少轮训练",
                "warning": "过多轮数会过拟合（验证集 Loss 上升）",
            },
            "gradient_accumulation_steps": {
                "purpose": "内存不足时模拟大 batch",
                "计算": "实际 batch = per_device_batch × accumulation_steps",
                "example": "batch=4, acc=8 → 实际 batch=32",
            }
        }


def recommend_hyperparams(dataset_size: int) -> dict:
    """根据数据集大小推荐超参数"""

    if dataset_size < 100:
        return {
            "learning_rate": 1e-4,  # 小数据用大 LR
            "num_train_epochs": 5,  # 多轮训练
            "lora_rank": 8,  # 小秩防止过拟合
        }
    elif dataset_size < 500:
        return {
            "learning_rate": 5e-5,
            "num_train_epochs": 3,
            "lora_rank": 16,
        }
    else:
        return {
            "learning_rate": 1e-5,  # 大数据用小 LR
            "num_train_epochs": 2,
            "lora_rank": 32,  # 大秩保留能力
        }


if __name__ == "__main__":
    tuner = BailianFineTuner()

    # 打印参数详解
    print("📚 微调参数详解：")
    for param, info in tuner.explain_parameters().items():
        print(f"\n{param}:")
        for key, value in info.items():
            print(f"  {key}: {value}")

    # 根据数据集推荐
    print("\n🎯 根据数据集大小推荐：")
    for size in [50, 200, 1000]:
        params = recommend_hyperparams(size)
        print(f"\n数据集 {size} 条：")
        print(json.dumps(params, indent=2))