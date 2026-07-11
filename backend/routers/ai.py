"""
统一 AI 路由 — POST /api/v1/ai/chat (SSE 流式)。
"""
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from schemas.ai import ChatAIRequest
from ai.agent_dispatcher import chat_pipeline, start_new_session

router = APIRouter(prefix="/ai", tags=["AI助手"])


@router.post("/chat")
async def ai_chat(req: ChatAIRequest):
    """统一 AI 聊天入口 — SSE 流式返回。

    支持意图：chat（文化问答）/ trip（行程规划）/ food（美食推荐）/ heritage（非遗查询）

    回复通过 SSE 事件流发送：
    - thinking: AI 正在思考
    - ask: 多轮追问
    - token: 流式文本
    - trip_card: 行程方案卡片
    - food_card: 美食推荐卡片
    - heritage_card: 非遗卡片
    - done: 本轮完成
    - error: 错误信息
    """
    session_id = req.session_id or uuid.uuid4().hex[:16]

    return StreamingResponse(
        chat_pipeline(session_id, req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/new")
async def new_chat_session(session_id: str = None):
    """开始新的 AI 对话，清除多轮追问状态。"""
    if session_id:
        await start_new_session(session_id)
    return {"code": 0, "message": "ok"}
