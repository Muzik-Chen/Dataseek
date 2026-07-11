"""
智能客服路由 — 对话消息/会话管理/历史记录。
比赛阶段 AI 回复为占位/模拟实现，后续接入 LangChain RAG。
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, distinct, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.chat import ChatMessage
from schemas.chat import (
    ChatMessageOut, ChatSendRequest, ChatSendOut,
    ChatSessionOut, ChatHistoryParams,
)
from utils.response import success, paginated

router = APIRouter(prefix="/chat", tags=["智能客服"])


# --- 知识库占位数据（后续替换为 RAG 向量检索） ---
KNOWLEDGE_BASE = {
    "牛肉火锅": "潮汕牛肉火锅以新鲜为主，牛肉从屠宰到上桌不超过4小时。推荐部位：吊龙、匙柄、胸口朥。热门店铺：八合里海记、福合埕。",
    "工夫茶": "潮汕工夫茶是中国茶道的活化石，讲究'二十一式'冲泡技法。核心：沸水、热罐、高冲低斟。常用茶叶：凤凰单丛、铁观音。",
    "英歌舞": "英歌舞是国家级非遗，融合武术、舞蹈、戏曲，表演者画脸谱、持英歌槌，阵型多变。最盛大的表演在春节至元宵期间。",
    "潮剧": "潮剧是用潮州方言演唱的古老剧种，属南戏分支，有500多年历史。代表剧目：《荔镜记》《苏六娘》《张春郎削发》。",
    "嵌瓷": "嵌瓷是潮汕特有的建筑装饰工艺，用彩色碎瓷片在屋顶、墙壁拼贴出人物花鸟，色彩鲜艳百年不掉。大寮嵌瓷是国家级非遗。",
    "潮汕": "潮汕地区包括汕头、潮州、揭阳三市，位于广东省东部沿海。文化特色：工夫茶、潮剧、英歌舞、潮汕美食、嵌瓷、木雕、抽纱、潮绣。",
    "美食": "潮汕是'中国美食之乡'。必尝：牛肉火锅、肠粉、粿条汤、蚝烙、卤鹅、鱼饭、鸭母捻、甜汤。热门美食街：汕头小公园、潮州牌坊街。",
    "旅游": "推荐景点：汕头南澳岛、潮州广济桥（湘子桥）、潮州古城、揭阳学宫、汕头礐石风景区。最佳旅游季节：10月-次年4月。",
    "节日": "潮汕重要民俗节日：春节营老爷（正月初一至十五）、元宵花灯、清明祭祖、端午赛龙舟、中秋拜月娘、冬至吃冬节丸。",
}

# 欢迎语
WELCOME_MESSAGE = "您好！我是潮汕文化小助手 🍵 可以问我关于潮汕美食、非遗、旅游、民俗等任何问题～"


@router.post("/send")
async def send_message(
    req: ChatSendRequest,
    db: AsyncSession = Depends(get_db),
):
    """发送消息并获取 AI 回复。"""
    session_id = req.session_id or uuid.uuid4().hex[:16]

    # 保存用户消息
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)

    # --- AI 回复逻辑（占位：关键词匹配，后续接入 LangChain RAG） ---
    reply = _generate_reply(req.message)
    sources = _find_sources(req.message)

    # 保存 AI 回复
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=reply,
    )
    db.add(assistant_msg)
    await db.flush()

    return success(ChatSendOut(
        session_id=session_id,
        reply=reply,
        sources=sources,
    ).model_dump())


@router.get("/history")
async def list_chat_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有会话列表。"""
    # 获取每个 session 的最新消息和计数
    subq = (
        select(
            ChatMessage.session_id,
            func.max(ChatMessage.created_at).label("updated_at"),
            func.count(ChatMessage.id).label("message_count"),
        )
        .group_by(ChatMessage.session_id)
        .subquery()
    )

    q = (
        select(ChatMessage.session_id, subq.c.updated_at, subq.c.message_count)
        .join(subq, ChatMessage.session_id == subq.c.session_id)
        .order_by(desc(subq.c.updated_at))
        .distinct()
    )

    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)

    rows = (await db.execute(q)).all()

    items = []
    for row in rows:
        # 获取该 session 的第一条用户消息作为标题
        first_msg = (await db.execute(
            select(ChatMessage).where(
                ChatMessage.session_id == row.session_id,
                ChatMessage.role == "user",
            ).order_by(ChatMessage.created_at.asc()).limit(1)
        )).scalar()

        # 获取最后一条消息
        last_msg = (await db.execute(
            select(ChatMessage).where(
                ChatMessage.session_id == row.session_id,
            ).order_by(ChatMessage.created_at.desc()).limit(1)
        )).scalar()

        items.append(ChatSessionOut(
            session_id=row.session_id,
            title=first_msg.content[:30] if first_msg else "新会话",
            last_message=last_msg.content[:50] if last_msg else "",
            message_count=row.message_count,
            updated_at=row.updated_at,
        ).model_dump())

    return paginated(items, len(items), page, page_size)


@router.get("/history/{session_id}")
async def get_chat_session(
    session_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """获取某个会话的完整消息记录。"""
    q = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)

    rows = (await db.execute(q)).scalars().all()
    count = len(rows)
    items = [ChatMessageOut.model_validate(r).model_dump() for r in rows]

    return paginated(items, count, page, page_size)


@router.get("/welcome")
async def get_welcome():
    """获取客服欢迎语和推荐问题。"""
    return success({
        "welcome": WELCOME_MESSAGE,
        "suggestions": [
            "潮汕有什么必吃的美食？",
            "工夫茶有什么讲究？",
            "英歌舞是什么？",
            "推荐一条3天的旅游路线",
            "潮汕有哪些非遗项目？",
        ],
    })


# --- 占位 AI ---
def _generate_reply(message: str) -> str:
    """简单的关键词匹配回复（后续替换为 LLM）。"""
    msg = message.strip()
    for keyword, answer in sorted(KNOWLEDGE_BASE.items(), key=lambda x: -len(x[0])):
        if keyword in msg:
            return answer
    return (
        f"关于「{msg[:30]}」，我还在学习中 📚\n\n"
        f"您可以尝试问我这些问题：\n"
        f"• 潮汕有什么好吃的？\n"
        f"• 工夫茶怎么泡？\n"
        f"• 推荐旅游路线\n"
        f"• 最近有什么民俗活动？"
    )


def _find_sources(message: str) -> list[dict]:
    """查找相关知识来源（后续替换为 RAG 向量检索）。"""
    sources = []
    msg = message.strip()
    for keyword in KNOWLEDGE_BASE:
        if keyword in msg:
            sources.append({"title": keyword, "type": "知识库"})
    return sources[:3]
