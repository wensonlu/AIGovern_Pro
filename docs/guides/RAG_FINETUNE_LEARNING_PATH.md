# RAG 问答模型微调学习路径

**目标：** 在 AIGovern Pro 项目中深入掌握 RAG 模型微调技术

**预计学习周期：** 4-6 周（业余时间）

---

## 🎯 学习目标检查清单

完成以下里程碑后，你将具备：

- [ ] 理解 LoRA/PEFT 微调原理
- [ ] 独立准备高质量训练数据集（200+ 条）
- [ ] 在云端平台完成至少 1 次成功微调
- [ ] 评估微调效果并优化参数
- [ ] 将微调模型集成到生产系统

---

## 📅 分阶段学习计划

### 第一阶段：理论基础（第 1-2 周）

#### 必读资源

**1. LoRA 论文与原理**
- [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
- [PEFT 官方文档](https://huggingface.co/docs/peft) - Parameter-Efficient Fine-Tuning

**2. RAG 特定知识**
- [Retrieval-Augmented Generation for Knowledge-Intensive Tasks](https://arxiv.org/abs/2005.11401)
- [RAGAS 评估框架](https://docs.ragas.io/) - RAG 质量评估标准

**3. 微调最佳实践**
- [阿里云百炼微调指南](https://help.aliyun.com/document_detail/2712215.html)
- [ModelScope 微调教程](https://modelscope.cn/docs/%E6%A8%A1%E5%9E%8B%E5%BE%AE%E8%B0%83)

#### 学习检查点

- [ ] 能解释 LoRA 的核心思想（低秩分解）
- [ ] 理解 RAGAS 四大评估指标（Faithfulness、Answer Relevance 等）
- [ ] 知道什么场景适合微调 vs 直接使用 RAG

---

### 第二阶段：数据准备（第 3 周）

#### 实战任务

**1. 数据采集**
- 从 AIGovern Pro 历史对话中提取 50 个真实问题
- 人工标注标准答案和相关文档

**2. 数据扩充**
- 运行 `backend/scripts/ai_data_augmentation.py` 生成 200+ 问答对
- 人工审核 AI 生成数据的质量

**3. 数据格式化**
- 运行 `backend/scripts/generate_finetune_data.py` 导出 JSONL 格式
- 划分训练集（80%）和验证集（20%）

#### 数据质量标准

- [ ] 每个问题至少有 1 个相关文档支撑
- [ ] 答案包含明确的文档引用
- [ ] 问题覆盖多种类型（事实型、解释型、操作型）
- [ ] 数据集不少于 200 条（最小可行规模）

#### 检查点

```bash
# 验证数据格式
python -c "
import json
with open('backend/data/finetune/rag_train_v1.jsonl') as f:
    for line in f:
        data = json.loads(line)
        assert 'instruction' in data
        assert 'input' in data
        assert 'output' in data
print('✅ 数据格式正确')
"
```

---

### 第三阶段：云端微调实践（第 4 周）

#### 方案 A：阿里云百炼（推荐初学者）

**操作步骤：**

1. **注册与配置**
   - 开通阿里云百炼服务
   - 获取 API Key
   - 创建 OSS bucket 存储训练数据

2. **上传数据**
   ```bash
   # 使用 ossutil 上传
   ossutil cp backend/data/finetune/rag_train_v1.jsonl oss://your-bucket/train.jsonl
   ossutil cp backend/data/finetune/rag_val_v1.jsonl oss://your-bucket/val.jsonl
   ```

3. **配置微调参数**
   - 运行 `backend/scripts/bailian_finetune_config.py`
   - 根据数据集大小调整超参数（参考脚本输出）

4. **提交训练任务**
   - 选择基础模型：Qwen-7B-Chat
   - 设置训练时长预算：约 2-4 小时
   - 监控训练 Loss 曲线

5. **获取微调模型**
   - 训练完成后获得模型 ID
   - 测试 API 调用

**预期成本：** 50-200 元（根据训练时长）

#### 方案 B：ModelScope（适合进阶学习）

**操作步骤：**

1. **本地环境准备**
   ```bash
   pip install modelscope transformers peft
   ```

2. **参考指南**
   - 阅读 `backend/docs/modelscope_finetune_guide.md`
   - 理解 LoRA 参数配置

3. **启动训练**
   ```bash
   python backend/scripts/modelscope_finetune.py
   ```

4. **上传模型**
   - 将微调模型上传到 ModelScope Hub
   - 获得 API 访问端点

**预期成本：** 免费（社区资源）或按量计费（云端 GPU）

#### 检查点

- [ ] 微调任务成功完成
- [ ] 训练 Loss 正常下降（无爆炸或 NaN）
- [ ] 验证集 Loss 未上升（未过拟合）
- [ ] 能通过 API 调用微调模型

---

### 第四阶段：评估与优化（第 5 周）

#### 评估流程

1. **准备测试集**
   - 20-50 条人工标注的高质量问答对
   - 覆盖不同难度和场景

2. **运行评估脚本**
   ```bash
   python backend/scripts/rag_evaluation.py
   ```

3. **分析评估报告**
   - 对比基线模型 vs 微调模型
   - 关注四大指标提升

#### 优化策略

**如果效果不理想（提升 < 5%）：**

- [ ] 检查数据质量（是否有噪声）
- [ ] 调整超参数（学习率、LoRA rank）
- [ ] 增加训练数据（目标 500+ 条）
- [ ] 尝试更大的基础模型（Qwen-14B）

**如果过拟合（验证集 Loss 上升）：**

- [ ] 减少训练轮数
- [ ] 降低 LoRA rank
- [ ] 增加 dropout
- [ ] 扩充数据集

#### 检查点

- [ ] 生成完整评估报告
- [ ] 微调模型在至少 2 个指标上优于基线
- [ ] 理解为什么某些指标提升，某些没提升

---

### 第五阶段：生产集成（第 6 周）

#### 集成步骤

1. **修改配置**
   ```python
   # backend/app/core/config.py
   USE_FINETUNED_MODEL = True
   FINETUNED_MODEL_NAME = "your-model-id"
   ```

2. **部署策略**
   - 初期：A/B 测试（20% 流量使用微调模型）
   - 中期：灰度发布（50% 流量）
   - 后期：全量上线（监控关键指标）

3. **监控指标**
   - 用户满意度（点赞率）
   - 回答准确率（人工抽检）
   - API 响应时间
   - 错误率

#### 回滚方案

```python
# 如果微调模型表现不佳，快速回滚
USE_FINETUNED_MODEL = False  # 切回基线模型
```

#### 检查点

- [ ] 微调模型成功部署到测试环境
- [ ] A/B 测试运行 1 周，数据正向
- [ ] 生产环境全量上线
- [ ] 监控仪表盘正常运行

---

## 🛠️ 工具与脚本清单

| 文件 | 用途 | 阶段 |
|------|------|------|
| `backend/scripts/generate_finetune_data.py` | 生成训练数据 | 第二阶段 |
| `backend/scripts/ai_data_augmentation.py` | AI 辅助扩充数据集 | 第二阶段 |
| `backend/scripts/bailian_finetune_config.py` | 百炼平台配置 | 第三阶段 |
| `backend/docs/modelscope_finetune_guide.md` | ModelScope 指南 | 第三阶段 |
| `backend/scripts/rag_evaluation.py` | 模型评估 | 第四阶段 |
| `backend/scripts/integrate_finetuned_model.py` | 系统集成 | 第五阶段 |

---

## 📖 进阶学习资源

### 理论深入

- [Fine-tuning LLMs with LoRA and QLoRA](https://www.philschmid.de/fine-tune-flan-t5-peft) - 实战教程
- [Advanced RAG Techniques](https://blog.langchain.dev/deconstructing-rag/) - LangChain 官方博客

### 开源工具

- [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) - 统一微调框架
- [Axolotl](https://github.com/OpenAccess-AI-Collective/axolotl) - 高级微调工具

### 社区

- [ModelScope 社区](https://modelscope.cn/) - 中文模型社区
- [Hugging Face PEFT](https://github.com/huggingface/peft) - 官方 PEFT 库

---

## 🎓 学习成果验收

完成所有阶段后，你将获得：

1. **理论能力**
   - 能向他人讲解 LoRA 原理
   - 理解何时微调、何时用 RAG

2. **实战能力**
   - 独立完成数据准备 → 微调 → 评估 → 部署全流程
   - 能诊断训练问题（过拟合、欠拟合）

3. **产出物**
   - 200+ 条高质量标注数据集
   - 1 个微调后的 RAG 问答模型
   - 完整评估报告

---

## 💡 学习建议

### 时间分配

- **工作日**：每天 1-2 小时（理论学习、代码阅读）
- **周末**：半天集中实践（数据准备、微调训练）

### 常见陷阱

❌ **跳过数据质量检查** → 微调效果差，浪费时间
❌ **盲目调参** → 不理解原理，无法优化
❌ **忽视评估** → 不知道模型是否真的变好

### 成功要素

✅ **数据优先** - 高质量数据 > 复杂算法
✅ **小步快跑** - 先用小数据集验证流程，再扩充
✅ **记录实验** - 每次微调记录参数和结果

---

**开始日期：** _________
**预计完成：** _________
**实际完成：** _________

**备注：**
___________________________________