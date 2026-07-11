"""
Agent 调度器 — 接收 IntentRouter 结果 → 调用对应 Agent → 包装为 SSE 事件流。

SSE 事件类型说明：
  - thinking:    AI 正在思考（前端展示加载动画 + label 文本）
  - ask:         多轮追问（前端展示选项按钮）
  - token:       流式文本 token（前端打字机效果逐字追加）
  - trip_card:   单张行程方案卡片（渐进式输出，每完成一套即刻发送）
  - food_card:   美食推荐卡片组
  - done:        本轮对话完成
  - error:       错误信息
"""
import json
from datetime import datetime
from typing import AsyncGenerator

from ai.intent_router import route_intent, clear_session
from ai.trip_agent import generate_trip_plans_stream
from ai.food_recommend import recommend_foods
from ai.cs_agent import chat_stream as cs_chat_stream
from database import async_session_factory
from models.chat import ChatMessage

from ai.prompts import sse_event


async def _persist_message(session_id: str, role: str, content: str, user_id: int | None = None):
    """写入一条消息到 chat_messages 并更新 chat_sessions。"""
    if not content or not session_id:
        return
    from models.session import ChatSession
    from sqlalchemy import select
    async with async_session_factory() as db:
        db.add(ChatMessage(session_id=session_id, role=role, content=content))
        # 确保 chat_sessions 行存在
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        if not result.scalar():
            db.add(ChatSession(
                session_id=session_id,
                user_id=user_id,
                title=content[:30] if role == 'user' else '新对话',
                status='active',
            ))
        else:
            # update updated_at
            row = result.scalar()
            row.updated_at = datetime.now()
        await db.commit()


async def chat_pipeline(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    """统一 AI 聊天管线 — SSE 事件流生成器。

    Usage in FastAPI router:
        return StreamingResponse(
            chat_pipeline(session_id, message),
            media_type="text/event-stream",
        )
    """
    # Step 1: 意图识别
    intent_result = await route_intent(session_id, user_message)

    # Step 2: 如果参数不全 → 追问
    if intent_result.missing_params:
        follow_up = intent_result.follow_up_question or ''
        yield sse_event(
            "ask",
            question=follow_up,
            options=intent_result.quick_options,
            intent=intent_result.intent,
            intents=intent_result.intents,
        )
        # Persist ask exchange
        await _persist_message(session_id, 'user', user_message)
        await _persist_message(session_id, 'assistant', follow_up)
        yield sse_event(
            "done",
            session_id=session_id,
            intent=intent_result.intent,
            intents=intent_result.intents,
        )
        return

    # Step 3: 参数齐全 → 分发到对应 Agent
    intent = intent_result.intent
    params = intent_result.extracted_params
    # 防御：确保 params 始终为 dict
    if not isinstance(params, dict):
        params = {}

    if intent == "trip":
        # === 行程规划：流式开场白 + 渐进式卡片输出 ===
        try:
            async for event_str in generate_trip_plans_stream(
                params,
                interest_hints=intent_result.interest_hints,
            ):
                yield event_str
        except Exception as e:
            yield sse_event("error", message=f"行程规划失败: {str(e)}")

    elif intent == "food":
        yield sse_event("thinking", label="正在为您寻找最合适的美食...")
        try:
            from database import async_session_factory
            from sqlalchemy import select
            from models.food import Food

            async with async_session_factory() as db:
                foods_q = await db.execute(
                    select(Food).where(Food.is_recommended == True).limit(50)
                )
                foods = foods_q.scalars().all()
                foods_list = [
                    {
                        "food_id": f.id,
                        "name": f.name,
                        "type": f.type,
                        "category_name": "",
                        "price_range": f.price_range or "",
                        "tags": f.tags or [],
                        "image_url": f.image_url or "",
                    }
                    for f in foods
                ]

            result = await recommend_foods(
                params.get("preference", user_message),
                foods_list,
            )
            # 属性映射：food_id → id, 加上 image_url
            enriched = []
            for r in result.get("recommendations", []):
                fid = r.get("food_id")
                match = next((f for f in foods_list if f["food_id"] == fid), None)
                enriched.append({
                    **r,
                    "id": fid,
                    "image_url": match.get("image_url", "") if match else "",
                })
            yield sse_event("food_card", items=enriched, summary=result.get("summary", ""))
            await _persist_message(session_id, 'user', user_message)
            await _persist_message(session_id, 'assistant', json.dumps(result, ensure_ascii=False))
        except Exception as e:
            yield sse_event("error", message=f"美食推荐失败: {str(e)}")

    elif intent == "heritage":
        yield sse_event("thinking", label="正在查阅非遗资料...")
        # heritage 复用 cs_agent 的 RAG 流式
        async for event_str in cs_chat_stream(session_id, user_message):
            yield event_str

    elif intent == "festival":
        yield sse_event("thinking", label="正在查阅民俗节庆资料...")
        # festival 复用 cs_agent 的 RAG 流式
        async for event_str in cs_chat_stream(session_id, user_message):
            yield event_str

    else:  # chat
        async for event_str in cs_chat_stream(session_id, user_message):
            yield event_str

    # Step 4: 完成信号（含多意图列表）
    yield sse_event(
        "done",
        session_id=session_id,
        intent=intent,
        intents=intent_result.intents,
    )


async def start_new_session(session_id: str):
    """开始新会话，清除多轮状态。"""
    await clear_session(session_id)
