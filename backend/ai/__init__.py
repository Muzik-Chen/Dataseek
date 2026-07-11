"""
AI 模块 — LangChain/LangGraph 集成 + RAG 知识库 + Prompt 工程。

架构:
- llm.py: LLM 提供商适配（Qwen / DeepSeek）
- embeddings.py: BGE 中文 Embedding 模型
- vector_store.py: FAISS 向量库构建与加载
- cs_agent.py: 智能客服 RAG Chain + SSE 流式
- trip_agent.py: 行程规划 LangGraph Agent
- food_recommend.py: 美食推荐 LLM Chain + 规则降级
- prompts/: 各场景 Prompt 模板
- knowledge/: RAG 知识库 Markdown 文档
"""
