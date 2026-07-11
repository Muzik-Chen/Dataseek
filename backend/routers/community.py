"""
社区推荐路由 — 动态/评论/点赞。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.community import CommunityPost, PostComment, PostLike
from models.user import User
from schemas.community import (
    PostCreate, PostOut, PostListParams,
    CommentCreate, CommentOut, CommentListParams,
)
from utils.response import success, paginated
from utils.dependencies import get_current_user, get_optional_user

router = APIRouter(prefix="/community", tags=["社区推荐"])


# --- 辅助：查用户昵称 ---
async def _get_user_map(db: AsyncSession, user_ids: set[int]) -> dict:
    if not user_ids:
        return {}
    users = (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()
    return {u.id: {"nickname": u.nickname, "avatar_url": u.avatar_url} for u in users}


def _enrich_post(post: CommunityPost, user_map: dict, is_liked: bool = False) -> dict:
    u = user_map.get(post.user_id, {})
    d = PostOut.model_validate(post).model_dump()
    d["user_nickname"] = u.get("nickname", "")
    d["user_avatar"] = u.get("avatar_url", "")
    d["is_liked"] = is_liked
    return d


# ===== 动态 =====
@router.get("/posts")
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    post_type: str | None = None,
    tag: str | None = None,
    keyword: str | None = None,
    sort: str = "created_at",
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """获取社区动态列表。"""
    q = select(CommunityPost)
    count_q = select(func.count(CommunityPost.id))

    if post_type:
        q = q.where(CommunityPost.post_type == post_type)
        count_q = count_q.where(CommunityPost.post_type == post_type)
    if keyword:
        q = q.where(
            CommunityPost.title.contains(keyword) | CommunityPost.content.contains(keyword)
        )
        count_q = count_q.where(
            CommunityPost.title.contains(keyword) | CommunityPost.content.contains(keyword)
        )

    # 排序
    sort_map = {
        "created_at": CommunityPost.created_at.desc(),
        "like_count": CommunityPost.like_count.desc(),
        "comment_count": CommunityPost.comment_count.desc(),
    }
    q = q.order_by(sort_map.get(sort, CommunityPost.created_at.desc()))

    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)

    total = (await db.execute(count_q)).scalar()
    rows = (await db.execute(q)).scalars().all()

    user_ids = {r.user_id for r in rows}
    user_map = await _get_user_map(db, user_ids)

    # 如果登录用户，查询点赞状态
    liked_ids = set()
    if current_user:
        post_ids = [r.id for r in rows]
        likes = (await db.execute(
            select(PostLike.post_id).where(
                PostLike.user_id == current_user.id,
                PostLike.post_id.in_(post_ids),
            )
        )).scalars().all()
        liked_ids = set(likes)

    items = [_enrich_post(r, user_map, r.id in liked_ids) for r in rows]
    return paginated(items, total, page, page_size)


@router.get("/posts/{post_id}")
async def get_post(
    post_id: int,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """获取动态详情。"""
    post = (await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))).scalar()
    if not post:
        raise HTTPException(status_code=404, detail="动态不存在")

    # 浏览量 +1
    post.view_count += 1
    await db.flush()

    user_map = await _get_user_map(db, {post.user_id})
    is_liked = False
    if current_user:
        like = (await db.execute(
            select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == current_user.id)
        )).scalar()
        is_liked = like is not None

    return success(_enrich_post(post, user_map, is_liked))


@router.post("/posts")
async def create_post(
    req: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发布社区动态。"""
    post = CommunityPost(
        user_id=current_user.id,
        title=req.title,
        content=req.content,
        images=req.images,
        tags=req.tags,
        post_type=req.post_type,
    )
    db.add(post)
    await db.flush()

    user_map = await _get_user_map(db, {current_user.id})
    return success(_enrich_post(post, user_map), "发布成功")


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除动态（仅作者本人）。"""
    post = (await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))).scalar()
    if not post:
        raise HTTPException(status_code=404, detail="动态不存在")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己的动态")

    # 同时删除关联的评论和点赞
    await db.execute(select(PostComment).where(PostComment.post_id == post_id).delete())
    await db.execute(select(PostLike).where(PostLike.post_id == post_id).delete())
    await db.delete(post)
    await db.flush()
    return success(message="已删除")


@router.put("/posts/{post_id}")
async def update_post(
    post_id: int,
    req: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """编辑动态（仅作者本人）。"""
    post = (await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))).scalar()
    if not post:
        raise HTTPException(status_code=404, detail="动态不存在")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能编辑自己的动态")

    post.title = req.title
    post.content = req.content
    post.images = req.images
    post.tags = req.tags
    post.post_type = req.post_type
    await db.flush()

    user_map = await _get_user_map(db, {current_user.id})
    return success(_enrich_post(post, user_map), "更新成功")


# ===== 评论 =====
@router.get("/posts/{post_id}/comments")
async def list_comments(
    post_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取动态的评论列表。"""
    q = (
        select(PostComment)
        .where(PostComment.post_id == post_id)
        .order_by(PostComment.created_at.asc())
    )
    count_q = select(func.count(PostComment.id)).where(PostComment.post_id == post_id)

    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)

    total = (await db.execute(count_q)).scalar()
    rows = (await db.execute(q)).scalars().all()

    user_ids = {r.user_id for r in rows}
    user_map = await _get_user_map(db, user_ids)

    items = []
    for r in rows:
        u = user_map.get(r.user_id, {})
        d = CommentOut.model_validate(r).model_dump()
        d["user_nickname"] = u.get("nickname", "")
        d["user_avatar"] = u.get("avatar_url", "")
        items.append(d)

    return paginated(items, total, page, page_size)


@router.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    req: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发表评论。"""
    post = (await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))).scalar()
    if not post:
        raise HTTPException(status_code=404, detail="动态不存在")

    comment = PostComment(
        post_id=post_id,
        user_id=current_user.id,
        content=req.content,
        parent_id=req.parent_id,
    )
    db.add(comment)

    # 更新评论数
    post.comment_count = (post.comment_count or 0) + 1
    await db.flush()

    user_map = await _get_user_map(db, {current_user.id})
    u = user_map.get(current_user.id, {})
    d = CommentOut.model_validate(comment).model_dump()
    d["user_nickname"] = u.get("nickname", "")
    d["user_avatar"] = u.get("avatar_url", "")

    return success(d, "评论成功")


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除评论（仅本人）。"""
    comment = (await db.execute(select(PostComment).where(PostComment.id == comment_id))).scalar()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己的评论")

    # 更新帖子的评论数
    post = (await db.execute(select(CommunityPost).where(CommunityPost.id == comment.post_id))).scalar()
    if post:
        post.comment_count = max(0, (post.comment_count or 0) - 1)

    await db.delete(comment)
    await db.flush()
    return success(message="已删除")


# ===== 点赞 =====
@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """点赞动态。"""
    post = (await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))).scalar()
    if not post:
        raise HTTPException(status_code=404, detail="动态不存在")

    existing = (await db.execute(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == current_user.id)
    )).scalar()
    if existing:
        raise HTTPException(status_code=400, detail="已点赞")

    db.add(PostLike(post_id=post_id, user_id=current_user.id))
    post.like_count = (post.like_count or 0) + 1
    await db.flush()
    return success({"liked": True, "like_count": post.like_count}, "点赞成功")


@router.delete("/posts/{post_id}/like")
async def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消点赞。"""
    like = (await db.execute(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == current_user.id)
    )).scalar()
    if not like:
        raise HTTPException(status_code=400, detail="未点赞")

    await db.delete(like)

    post = (await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))).scalar()
    if post:
        post.like_count = max(0, (post.like_count or 0) - 1)

    await db.flush()
    return success({"liked": False, "like_count": post.like_count if post else 0}, "已取消点赞")
