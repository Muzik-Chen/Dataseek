"""
智能客服 RAG Agent — LangChain 检索增强生成 + SSE 流式输出。

流程：
1. FAISS 向量检索 Top-3 相关知识
2. 拼接 System Prompt + 知识 + 对话历史 + 用户问题
3. LLM 流式生成 → SSE 逐 token 返回前端
"""
import json
import asyncio
from typing import AsyncGenerator
from fastapi.responses import StreamingResponse

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

from ai.llm import get_llm
from ai.vector_store import load_knowledge_base
from ai.prompts import CHAT_SYSTEM_PROMPT
from database import async_session_factory
from models.chat import ChatMessage

# === 全局单例 ===
_vector_store = None
_vector_store_failed = False


def _get_vector_store():
    global _vector_store, _vector_store_failed
    if _vector_store is None and not _vector_store_failed:
        try:
            _vector_store = load_knowledge_base()
            if _vector_store is None:
                _vector_store_failed = True
                print("[AI] 向量知识库不可用，使用纯 LLM 模式（无 RAG）")
            else:
                print("[AI] FAISS 知识库加载完成")
        except Exception as e:
            _vector_store_failed = True
            print(f"[AI] 向量知识库加载失败，将使用纯 LLM 模式（无 RAG）: {e}")
    return _vector_store


# === DBChatMessageHistory — DB 持久化对话历史 ===

class DBChatMessageHistory(BaseChatMessageHistory):
    """数据库持久化的对话历史（兼容 LangChain BaseChatMessageHistory 接口）。

    消息存储在 chat_messages 表中，按 created_at 排序。
    自动 trim 到 40 条（20 轮对话）。
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._cached_messages: list | None = None

    @property
    def messages(self):
        # LangChain 在运行时同步访问，依赖 _load_messages 预先加载
        if self._cached_messages is None:
            # 同步降级：返回空列表（首次调用前应通过 async init 加载）
            return []
        return self._cached_messages

    async def _load_messages(self):
        """异步从 DB 加载消息历史。"""
        from sqlalchemy import select
        async with async_session_factory() as db:
            result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == self.session_id)
                .order_by(ChatMessage.created_at.asc())
            )
            rows = result.scalars().all()
            msgs = []
            for r in rows:
                if r.role == 'user':
                    msgs.append(HumanMessage(content=r.content))
                elif r.role == 'assistant':
                    msgs.append(AIMessage(content=r.content))
            self._cached_messages = msgs[-40:]  # trim 到最近 20 轮

    def add_messages(self, messages):
        """同步写入（LangChain 接口要求）— 异步写入通过 _persist_messages 延迟执行。"""
        if self._cached_messages is None:
            self._cached_messages = []
        self._cached_messages.extend(messages)
        # 只保留最近 40 条
        if len(self._cached_messages) > 40:
            self._cached_messages = self._cached_messages[-40:]
        # 标记需要持久化
        self._dirty = True

    async def _persist_messages(self):
        """将缓存的消息异步持久化到 DB。"""
        if not hasattr(self, '_dirty') or not self._dirty:
            return
        from sqlalchemy import select, delete
        async with async_session_factory() as db:
            # 删除旧消息，重新写入（简化方案）
            await db.execute(
                delete(ChatMessage).where(ChatMessage.session_id == self.session_id)
            )
            for msg in (self._cached_messages or []):
                role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
                db.add(ChatMessage(
                    session_id=self.session_id,
                    role=role,
                    content=msg.content,
                ))
            await db.commit()
        self._dirty = False

    def clear(self):
        self._cached_messages = []
        self._dirty = True


async def _get_history(session_id: str) -> DBChatMessageHistory:
    """获取或创建 DBChatMessageHistory 实例（异步加载消息）。"""
    history = DBChatMessageHistory(session_id)
    await history._load_messages()
    return history


# === System Prompt（已迁移至 ai.prompts.chat） ===


async def build_rag_chain():
    """构建 RAG Chain（启动时调用）。"""
    llm = get_llm(temperature=0.7, streaming=True)

    prompt = ChatPromptTemplate.from_messages([
        ("system", CHAT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])

    chain = prompt | llm

    # 使用 _sync_get_history wrapper：在 async 上下文中通过 event loop 加载 DB 历史
    chain_with_history = RunnableWithMessageHistory(
        chain,
        _sync_get_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    return chain_with_history


# === 同步 history factory（供 LangChain RunnableWithMessageHistory 使用） ===

# 预加载的消息缓存（在 chat_stream 中异步加载，在 _PreloadedHistory 中同步消费）
_preloaded_histories: dict[str, list] = {}

class _PreloadedHistory(BaseChatMessageHistory):
    """从预加载缓存读取消息历史（绕过 LangChain 同步限制）。"""

    def __init__(self, session_id: str):
        self.session_id = session_id

    @property
    def messages(self):
        return _preloaded_histories.get(self.session_id, [])

    def add_messages(self, messages):
        msgs = _preloaded_histories.get(self.session_id, [])
        msgs.extend(messages)
        if len(msgs) > 40:
            _preloaded_histories[self.session_id] = msgs[-40:]
        else:
            _preloaded_histories[self.session_id] = msgs

    def clear(self):
        _preloaded_histories[self.session_id] = []


def _sync_get_history(session_id: str) -> BaseChatMessageHistory:
    """同步历史工厂（LangChain 要求）。"""
    return _PreloadedHistory(session_id)


_rag_chain = None


def _get_rag_chain():
    global _rag_chain
    if _rag_chain is None:
        raise RuntimeError("RAG chain 尚未初始化，请在 FastAPI startup 中调用 build_rag_chain()")
    return _rag_chain


async def init_rag_chain():
    """FastAPI 启动时初始化 RAG Chain。"""
    global _rag_chain
    _rag_chain = await build_rag_chain()


async def chat_stream(
    session_id: str,
    user_message: str,
) -> AsyncGenerator[str, None]:
    """SSE 流式返回 AI 客服回复。

    Yields:
        SSE 格式的事件字符串：
        - {"type": "sources", "sources": [...]}
        - {"type": "token", "content": "..."}
        - {"type": "done", "session_id": "..."}
    """
    # Step 1: 检索相关知识（向量库不可用时跳过）
    vector_store = _get_vector_store()
    if vector_store is not None:
        try:
            docs = vector_store.similarity_search(user_message, k=3)
            knowledge_context = "\n---\n".join([d.page_content[:800] for d in docs])
            sources = [
                {"title": d.metadata.get("title", ""), "source": d.metadata.get("source", "")}
                for d in docs
            ]
        except Exception:
            knowledge_context = "（知识库暂时不可用）"
            sources = []
    else:
        knowledge_context = "（知识库暂时不可用，我将基于自身知识回答）"
        sources = []

    yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"

    # Pre-load DB history into cache（在 chain 调用前异步加载）
    history = DBChatMessageHistory(session_id)
    await history._load_messages()
    _preloaded_histories[session_id] = list(history._cached_messages or [])

    # Step 2: 流式生成
    try:
        chain = _get_rag_chain()
    except RuntimeError:
        # RAG Chain 未初始化 → 纯 LLM 降级
        from ai.llm import get_llm
        llm = get_llm(temperature=0.7, streaming=True)
        prompt = f"""你是一个潮汕文化宣传助手，名叫"潮小文"。
请回答用户问题，语气亲切、简洁生动，控制在 200-400 字。

用户问题：{user_message}"""
        try:
            async for chunk in llm.astream(prompt):
                token = chunk.content if hasattr(chunk, "content") else str(chunk)
                if token:
                    yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        return

    full_response = ""

    try:
        async for chunk in chain.astream(
            {
                "context": knowledge_context,
                "input": user_message,
            },
            config={"configurable": {"session_id": session_id}},
        ):
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            if token:
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        return

    # Persist messages to DB — sync from _PreloadedHistory cache first
    msgs = _preloaded_histories.get(session_id, [])
    if msgs:
        history._cached_messages = msgs
        await history._persist_messages()

    # Step 3: 完成信号
    yield f"data: {json.dumps({'type': 'done', 'session_id': session_id}, ensure_ascii=False)}\n\n"


def create_sse_response(session_id: str, user_message: str) -> StreamingResponse:
    """创建 FastAPI StreamingResponse 用于 SSE 端点。"""
    return StreamingResponse(
        chat_stream(session_id, user_message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def get_session_history(session_id: str) -> list[dict]:
    """获取会话历史消息列表（从 DB）。"""
    from sqlalchemy import select
    async with async_session_factory() as db:
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        rows = result.scalars().all()
        return [
            {"role": r.role, "content": r.content}
            for r in rows
        ]
