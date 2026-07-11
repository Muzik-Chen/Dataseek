"""
私信路由 — 会话列表/消息记录/发送消息。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, or_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.message import PrivateMessage
from models.user import User
from schemas.message import MessageSend, MessageOut, ConversationOut
from utils.response import success, paginated
from utils.dependencies import get_current_user

router = APIRouter(prefix="/messages", tags=["私信"])


@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的会话列表。"""
    # 找到所有与我有过对话的用户
    sent_to = select(
        PrivateMessage.receiver_id.label("other_id"),
        func.max(PrivateMessage.created_at).label("updated_at"),
    ).where(PrivateMessage.sender_id == current_user.id).group_by(PrivateMessage.receiver_id)

    received_from = select(
        PrivateMessage.sender_id.label("other_id"),
        func.max(PrivateMessage.created_at).label("updated_at"),
    ).where(PrivateMessage.receiver_id == current_user.id).group_by(PrivateMessage.sender_id)

    # 合并并取最新
    union_q = sent_to.union_all(received_from).subquery()
    q = (
        select(union_q.c.other_id, func.max(union_q.c.updated_at).label("updated_at"))
        .group_by(union_q.c.other_id)
        .order_by(desc(func.max(union_q.c.updated_at)))
    )

    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)

    rows = (await db.execute(q)).all()

    # 批量获取用户信息
    other_ids = [r.other_id for r in rows]
    users = {}
    if other_ids:
        user_rows = (await db.execute(select(User).where(User.id.in_(other_ids)))).scalars().all()
        users = {u.id: u for u in user_rows}

    items = []
    for row in rows:
        u = users.get(row.other_id)
        # 获取最后一条消息和未读数
        last_msg = (await db.execute(
            select(PrivateMessage).where(
                or_(
                    and_(PrivateMessage.sender_id == current_user.id, PrivateMessage.receiver_id == row.other_id),
                    and_(PrivateMessage.sender_id == row.other_id, PrivateMessage.receiver_id == current_user.id),
                )
            ).order_by(desc(PrivateMessage.created_at)).limit(1)
        )).scalar()

        unread = (await db.execute(
            select(func.count(PrivateMessage.id)).where(
                PrivateMessage.sender_id == row.other_id,
                PrivateMessage.receiver_id == current_user.id,
                PrivateMessage.is_read == False,
            )
        )).scalar()

        items.append(ConversationOut(
            user_id=row.other_id,
            user_nickname=u.nickname if u else "",
            user_avatar=u.avatar_url if u else "",
            last_message=last_msg.content[:50] if last_msg else "",
            unread_count=unread or 0,
            updated_at=row.updated_at,
        ).model_dump())

    return paginated(items, len(items), page, page_size)


@router.get("/{other_user_id}")
async def get_messages(
    other_user_id: int,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    before_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取与某用户的私信记录。"""
    q = select(PrivateMessage).where(
        or_(
            and_(PrivateMessage.sender_id == current_user.id, PrivateMessage.receiver_id == other_user_id),
            and_(PrivateMessage.sender_id == other_user_id, PrivateMessage.receiver_id == current_user.id),
        )
    )

    if before_id:
        q = q.where(PrivateMessage.id < before_id)

    q = q.order_by(desc(PrivateMessage.created_at))
    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)

    rows = (await db.execute(q)).scalars().all()

    # 标记已读
    unread_ids = [
        r.id for r in rows
        if r.receiver_id == current_user.id and not r.is_read
    ]
    if unread_ids:
        for r in rows:
            if r.id in unread_ids:
                r.is_read = True
        await db.flush()

    items = [MessageOut.model_validate(r).model_dump() for r in reversed(rows)]
    return paginated(items, len(items), page, page_size)


@router.post("")
async def send_message(
    req: MessageSend,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发送私信。"""
    if req.receiver_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能给自己发消息")

    # 检查接收者是否存在
    receiver = (await db.execute(select(User).where(User.id == req.receiver_id))).scalar()
    if not receiver:
        raise HTTPException(status_code=404, detail="接收用户不存在")

    msg = PrivateMessage(
        sender_id=current_user.id,
        receiver_id=req.receiver_id,
        content=req.content,
    )
    db.add(msg)
    await db.flush()

    return success(MessageOut.model_validate(msg).model_dump(), "发送成功")


@router.put("/{msg_id}/read")
async def mark_read(
    msg_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记消息已读。仅接收者可操作。"""
    msg = (await db.execute(select(PrivateMessage).where(PrivateMessage.id == msg_id))).scalar()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    if msg.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能标记自己收到的消息")
    msg.is_read = True
    await db.flush()
    return success(message="已标记为已读")
