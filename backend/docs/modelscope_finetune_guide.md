"""
ModelScope 平台微调指南
平台地址：https://modelscope.cn/
"""

# ModelScope 微调流程

## 1. 环境准备

pip install modelscope
pip install transformers datasets peft

## 2. 选择基础模型

推荐模型：
- Qwen-7B-Chat（与你的项目兼容）
- ChatGLM3-6B（中文能力强）
- Baichuan2-7B-Chat（电商场景优化）

## 3. 本地微调脚本示例

from modelscope import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType

# 加载模型
model = AutoModelForCausalLM.from_pretrained(
    'qwen/Qwen-7B-Chat',
    device_map="auto",
    trust_remote_code=True
)
tokenizer = AutoTokenizer.from_pretrained('qwen/Qwen-7B-Chat')

# LoRA 配置
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,  # LoRA rank
    lora_alpha=32,
    lora_dropout=0.1,
    target_modules=["c_attn", "c_proj"]  # 注意力层
)

# 应用 LoRA
model = get_peft_model(model, lora_config)

# 训练（使用 Hugging Face Trainer）
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    learning_rate=5e-5,
    logging_steps=10,
    save_steps=100,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
)

trainer.train()

# 保存微调模型
model.save_pretrained("./aigovern-rag-finetuned")
tokenizer.save_pretrained("./aigovern-rag-finetuned")

## 4. ModelScope 云端训练（更简单）

# 上传数据集到 ModelScope
from modelscope.msdatasets import MsDataset

dataset = MsDataset.load(
    'your_dataset_name',
    subset_name='default',
    split='train'
)

# 在 ModelScope 平台提交训练任务
# 平台自动配置 GPU，一键训练

## 5. 模型上传与分享

from modelscope.hub.api import HubApi

api = HubApi()
api.push_model(
    model_id='your-name/aigovern-rag-v1',
    model_dir='./aigovern-rag-finetuned'
)

---

## ModelScope vs 百炼对比

| 特性 | ModelScope | 百炼 |
|------|-----------|------|
| **成本** | 免费（社区资源） | 按量计费 |
| **GPU** | 需要本地 GPU 或申请云端 | 无需 GPU |
| **模型选择** | 开源模型多 |阿里云官方模型 |
| **上手难度** | 需要技术背景 | 界面友好 |
| **集成难度** | 需要自己部署 | 直接 API 调用 |

**推荐策略：**
- 学习阶段 → ModelScope（免费实践）
- 生产部署 → 百炼（稳定服务）