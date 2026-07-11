"""
社区业务逻辑 — 动态/评论/点赞。
"""
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.community import CommunityPost, PostComment, PostLike
from models.user import User


async def _get_user_map(db: AsyncSession, user_ids: set[int]) -> dict:
    """批量获取用户信息。"""
    if not user_ids:
        return {}
    users = (await db.execute(
        select(User).where(User.id.in_(user_ids))
    )).scalars().all()
    return {u.id: {"nickname": u.nickname, "avatar_url": u.avatar_url} for u in users}


async def list_posts(
    db: AsyncSession,
    page: int = 1, page_size: int = 20,
    post_type: str | None = None,
    tag: str | None = None,
    keyword: str | None = None,
    sort: str = "created_at",
) -> tuple[list[CommunityPost], int]:
    """社区 Feed 流（分页+筛选+排序）。"""
    q = select(CommunityPost)
    count_q = select(func.count(CommunityPost.id))

    if post_type:
        q = q.where(CommunityPost.post_type == post_type)
        count_q = count_q.where(CommunityPost.post_type == post_type)
    if tag:
        # JSON 数组模糊匹配
        q = q.where(CommunityPost.tags.contains(tag))
        count_q = count_q.where(CommunityPost.tags.contains(tag))
    if keyword:
        q = q.where(
            CommunityPost.title.contains(keyword) |
            CommunityPost.content.contains(keyword)
        )
        count_q = count_q.where(
            CommunityPost.title.contains(keyword) |
            CommunityPost.content.contains(keyword)
        )

    sort_col = desc(CommunityPost.created_at)
    if sort == "like_count":
        sort_col = desc(CommunityPost.like_count)
    elif sort == "comment_count":
        sort_col = desc(CommunityPost.comment_count)
    q = q.order_by(sort_col)

    total = (await db.execute(count_q)).scalar()
    offset = (page - 1) * page_size
    rows = (await db.execute(q.offset(offset).limit(page_size))).scalars().all()
    return list(rows), total


async def get_post_detail(
    db: AsyncSession, post_id: int, current_user_id: int | None = None,
) -> dict:
    """获取动态详情 + 浏览数 +1。"""
    post = (await db.execute(
        select(CommunityPost).where(CommunityPost.id == post_id)
    )).scalar()
    if not post:
        raise ValueError("动态不存在")

    post.view_count = (post.view_count or 0) + 1

    user_map = await _get_user_map(db, {post.user_id})
    u = user_map.get(post.user_id, {})

    is_liked = False
    if current_user_id:
        like = (await db.execute(
            select(PostLike).where(
                PostLike.post_id == post_id,
                PostLike.user_id == current_user_id,
            )
        )).scalar()
        is_liked = like is not None

    return {
        "id": post.id,
        "user_id": post.user_id,
        "user_nickname": u.get("nickname", ""),
        "user_avatar": u.get("avatar_url", ""),
        "title": post.title,
        "content": post.content,
        "images": post.images,
        "tags": post.tags,
        "post_type": post.post_type,
        "view_count": post.view_count,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "is_liked": is_liked,
        "created_at": post.created_at.isoformat() if post.created_at else None,
    }


async def toggle_like(
    db: AsyncSession, post_id: int, user_id: int, action: str = "like",
) -> tuple[bool, int]:
    """点赞/取消点赞。返回 (liked, like_count)。"""
    post = (await db.execute(
        select(CommunityPost).where(CommunityPost.id == post_id)
    )).scalar()
    if not post:
        raise ValueError("动态不存在")

    existing = (await db.execute(
        select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == user_id,
        )
    )).scalar()

    if action == "like":
        if existing:
            raise ValueError("已点赞")
        db.add(PostLike(post_id=post_id, user_id=user_id))
        post.like_count = (post.like_count or 0) + 1
        return True, post.like_count
    else:
        if not existing:
            raise ValueError("未点赞")
        await db.delete(existing)
        post.like_count = max(0, (post.like_count or 0) - 1)
        return False, post.like_count
