"""
RAG 知识库 — 潮汕文化领域知识文档。

格式:
- .json: 结构化知识条目，每条含 name/category/description 及扩展字段
  - food_knowledge.json  — 25 条潮汕美食知识（含 famous_shops/price_range/tips）
  - culture_knowledge.json — 26 条非遗文化知识（含 level/region/best_viewing/tips）
- .md: 原始知识文档（保留作为补充参考）
  - chaoshan_food.md
  - chaoshan_culture.md

向量化流程:
  JSON 条目 → 拼接 name+category+description+扩展字段 → Document → FAISS 向量索引
"""
