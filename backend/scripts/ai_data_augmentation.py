"""
数据集扩充工具 - 多渠道生成训练数据
"""

import json
import asyncio
from typing import List, Dict
from app.core.llm import llm_client
from app.services.rag_service import RAGService


async def ai_generate_qa_pairs(document_text: str, num_pairs: int = 5) -> List[Dict]:
    """使用 AI 从文档自动生成问答对"""

    prompt = f"""请从以下文档中生成 {num_pairs} 个高质量的问答对。

文档内容：
{document_text}

要求：
1. 问题要具体、多样化（事实型、解释型、应用型）
2. 答案要准确、完整，基于文档内容
3. 标注答案在文档中的具体位置

输出 JSON 格式：
[
  {{
    "question": "...",
    "answer": "...",
    "source_text": "原文引用片段"
  }}
]
"""

    response = await llm_client.generate_text(prompt, max_tokens=2048)

    # 解析 JSON（可能包含 markdown 代码块）
    try:
        # 提取 JSON 内容
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        qa_pairs = json.loads(response.strip())
        return qa_pairs
    except:
        print("⚠️ JSON 解析失败，返回原始文本")
        return []


async def enrich_from_documents():
    """从知识库文档批量生成问答"""

    rag = RAGService()
    db = rag.db

    # 查询所有文档
    documents = db.execute("SELECT id, title, filename FROM documents LIMIT 10").fetchall()

    all_qa_pairs = []
    for doc in documents:
        # 检索文档内容
        chunks = db.execute(
            "SELECT chunk_text FROM document_chunks WHERE document_id = :id",
            {"id": doc.id}
        ).fetchall()

        doc_text = "\n".join([chunk.chunk_text for chunk in chunks])

        # AI 生成问答
        pairs = await ai_generate_qa_pairs(doc_text, num_pairs=3)

        for pair in pairs:
            all_qa_pairs.append({
                "document_id": doc.id,
                "document_title": doc.title,
                **pair
            })

        print(f"✅ 从文档 '{doc.title}' 生成 {len(pairs)} 个问答对")

    # 导出为 JSONL
    with open("backend/data/finetune/ai_generated_qa.jsonl", "w") as f:
        for item in all_qa_pairs:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n✅ 总计生成 {len(all_qa_pairs)} 个问答对")


# 运行示例
if __name__ == "__main__":
    asyncio.run(enrich_from_documents())