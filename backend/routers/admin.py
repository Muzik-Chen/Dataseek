"""
<<<<<<< HEAD
管理后台路由 — 基于 AdminResource 工厂 + 独立端点。
"""
import os
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from utils.dependencies import require_admin
from utils.response import success, paginated, error
from utils.security import mask_phone, mask_email

=======
管理后台路由 — 全部需要 admin 权限。
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
import json

from database import get_db
from utils.dependencies import get_current_user, require_admin
from utils.response import success_response, error_response
from utils.security import mask_phone, mask_email
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
from models.user import User
from models.food import Food, FoodCategory
from models.heritage import Heritage
from models.community import CommunityPost, PostComment
from models.dashboard import WeatherRecord, CrowdRecord
from models.chat import ChatMessage
from models.favorite import UserFavorite
from models.trip import TripPlan
<<<<<<< HEAD
from models.heritage import FolkEvent

from schemas.admin import (
    FoodAdminCreate, FoodAdminUpdate, FoodAdminOut, FoodAdminListItem,
    HeritageAdminCreate, HeritageAdminUpdate, HeritageAdminOut, HeritageAdminListItem,
    EventAdminCreate, EventAdminUpdate, EventAdminOut, EventAdminListItem,
    UserAdminUpdate, SettingsAdminUpdate,
)

from utils.admin_resource import AdminResource

router = APIRouter(prefix="/admin", tags=["管理后台"])

# ─────────────────────────────────────────────────────────
# AdminResource 工厂 — 自动生成标准 CRUD
# ─────────────────────────────────────────────────────────

food_admin = AdminResource(
    model=Food,
    schemas={
        "create": FoodAdminCreate,
        "update": FoodAdminUpdate,
        "out": FoodAdminOut,
        "list_item": FoodAdminListItem,
    },
    config={
        "prefix": "/foods",
        "search_fields": ["name", "description"],
        "filter_fields": ["category_id", "type", "is_recommended"],
    },
)

heritage_admin = AdminResource(
    model=Heritage,
    schemas={
        "create": HeritageAdminCreate,
        "update": HeritageAdminUpdate,
        "out": HeritageAdminOut,
        "list_item": HeritageAdminListItem,
    },
    config={
        "prefix": "/heritages",
        "search_fields": ["name", "description"],
        "filter_fields": ["category", "type", "region"],
    },
)

event_admin = AdminResource(
    model=FolkEvent,
    schemas={
        "create": EventAdminCreate,
        "update": EventAdminUpdate,
        "out": EventAdminOut,
        "list_item": EventAdminListItem,
    },
    config={
        "prefix": "/events",
        "search_fields": ["name", "description"],
        "filter_fields": ["event_type", "region"],
    },
)

# 注册工厂生成的 router
router.include_router(food_admin.get_router())
router.include_router(heritage_admin.get_router())
router.include_router(event_admin.get_router())


# ─────────────────────────────────────────────────────────
# 仪表盘
# ─────────────────────────────────────────────────────────

=======

router = APIRouter(prefix="/admin", tags=["管理后台"])


# === 仪表盘 ===
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """仪表盘统计数据。"""
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    total_foods = (await db.execute(select(func.count(Food.id)))).scalar()
    total_heritages = (await db.execute(select(func.count(Heritage.id)))).scalar()
    total_posts = (await db.execute(select(func.count(CommunityPost.id)))).scalar()
<<<<<<< HEAD
    total_events = (await db.execute(select(func.count(FolkEvent.id)))).scalar()

    # ai_calls_today — 从 chat_messages 按当天统计
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    ai_calls_today = (await db.execute(
        select(func.count(ChatMessage.id)).where(
            func.date(ChatMessage.created_at) == today
        )
    )).scalar()
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22

    # 近7天新增用户趋势
    new_users_7d = (await db.execute(
        text("SELECT DATE(created_at) as d, COUNT(*) as c FROM users WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) GROUP BY d ORDER BY d")
    )).fetchall()
    active_posts_7d = (await db.execute(
        text("SELECT DATE(created_at) as d, COUNT(*) as c FROM community_posts WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) GROUP BY d ORDER BY d")
    )).fetchall()

<<<<<<< HEAD
    return success(data={
=======
    return success_response(data={
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
        "total_users": total_users,
        "total_foods": total_foods,
        "total_heritages": total_heritages,
        "total_posts": total_posts,
<<<<<<< HEAD
        "total_events": total_events,
        "ai_calls_today": ai_calls_today or 0,
=======
        "ai_calls_today": 0,
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
        "new_users_7d": [{"date": str(r[0]), "count": r[1]} for r in new_users_7d],
        "active_posts_7d": [{"date": str(r[0]), "count": r[1]} for r in active_posts_7d],
    })


@router.get("/recent-activity")
async def get_recent_activity(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """最近动态。"""
    posts = (await db.execute(
        select(CommunityPost).order_by(CommunityPost.created_at.desc()).limit(10)
    )).scalars().all()
    msgs = (await db.execute(
        select(ChatMessage).order_by(ChatMessage.created_at.desc()).limit(10)
    )).scalars().all()

<<<<<<< HEAD
    return success(data={
=======
    return success_response(data={
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
        "posts": [{"id": p.id, "title": p.title, "post_type": p.post_type, "created_at": str(p.created_at)} for p in posts],
        "chat_messages": [{"id": m.id, "content": m.content[:50] if m.content else "", "role": m.role, "created_at": str(m.created_at)} for m in msgs],
    })


<<<<<<< HEAD
# ─────────────────────────────────────────────────────────
# 用户管理
# ─────────────────────────────────────────────────────────

=======
# === 用户管理 ===
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = Query(""),
    role: str = Query(""),
    persona_type: str = Query(""),
    is_disabled: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    q = select(User)
    if keyword:
        q = q.where(User.email.contains(keyword) | User.nickname.contains(keyword))
    if role:
        q = q.where(User.role == role)
    if persona_type:
        q = q.where(User.persona_type == persona_type)
    if is_disabled is not None:
        q = q.where(User.is_disabled == is_disabled)

    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar()

    rows = (await db.execute(
        q.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

<<<<<<< HEAD
    return paginated(
        items=[
=======
    return success_response(data={
        "items": [
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
            {
                "id": u.id, "email": mask_email(u.email), "phone": u.phone,
                "nickname": u.nickname,
                "persona_type": u.persona_type, "role": u.role,
                "is_disabled": u.is_disabled, "created_at": str(u.created_at),
            }
            for u in rows
        ],
<<<<<<< HEAD
        total=total, page=page, page_size=page_size,
    )
=======
        "total": total, "page": page, "page_size": page_size,
    })
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """用户详情（含收藏数+行程数+动态数）。"""
    user = await db.get(User, user_id)
    if not user:
<<<<<<< HEAD
        raise HTTPException(404, detail="用户不存在")

=======
        return error_response("E1006", "用户不存在")

    # 统计关联数据
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    fav_count = (await db.execute(
        select(func.count()).select_from(UserFavorite).where(UserFavorite.user_id == user_id)
    )).scalar()
    trip_count = (await db.execute(
        select(func.count()).select_from(TripPlan).where(TripPlan.user_id == user_id)
    )).scalar()
    post_count = (await db.execute(
        select(func.count()).select_from(CommunityPost).where(CommunityPost.user_id == user_id)
    )).scalar()

<<<<<<< HEAD
    return success(data={
=======
    return success_response(data={
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
        "id": user.id, "email": mask_email(user.email), "phone": user.phone,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url, "persona_type": user.persona_type,
        "interests": user.interests, "role": user.role,
        "is_disabled": user.is_disabled, "created_at": str(user.created_at),
        "favorites_count": fav_count, "trips_count": trip_count, "posts_count": post_count,
    })


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
<<<<<<< HEAD
    body: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """编辑用户（管理员可修改角色/禁用状态/用户类型）。"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, detail="用户不存在")

    update_data = body.model_dump(exclude_unset=True)

    # 禁止禁用管理员账号
    if update_data.get("is_disabled") and user.role == "admin":
        raise HTTPException(403, detail="不能禁用管理员账号")

    # Admin 唯一性检查
    if update_data.get("role") == "admin":
        existing_admin = (await db.execute(
            select(User).where(User.role == "admin", User.id != user_id)
        )).scalars().first()
        if existing_admin:
            raise HTTPException(409, detail="已存在管理员账号，系统仅允许一个管理员")

    for key, value in update_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return success(data={"id": user.id, "is_disabled": user.is_disabled, "role": user.role}, message="已更新")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """删除用户及关联数据。"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, detail="用户不存在")

    # 禁止删除唯一 admin
    if user.role == "admin":
        raise HTTPException(403, detail="不能删除唯一的管理员账号")

    # 级联清理：收藏、行程、帖子、评论、点赞、聊天消息
    from models.community import PostLike
    from models.favorite import UserFavorite
    from models.trip import TripPlan

    for rel_model, fk in [
        (UserFavorite, "user_id"),
        (TripPlan, "user_id"),
        (CommunityPost, "user_id"),
        (PostComment, "user_id"),
        (PostLike, "user_id"),
        (ChatMessage, "user_id"),
    ]:
        rels = (await db.execute(
            select(rel_model).where(getattr(rel_model, fk) == user_id)
        )).scalars().all()
        for r in rels:
            await db.delete(r)

    await db.delete(user)
    await db.commit()
    return success(message="用户及关联数据已删除")


# ─────────────────────────────────────────────────────────
# 社区审核（保持不变 — 结构特殊不走工厂）
# ─────────────────────────────────────────────────────────

=======
    is_disabled: bool | None = Form(None),
    role: str | None = Form(None),
    persona_type: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """编辑用户（管理员可修改角色/禁用状态/用户类型，不可改密码和邮箱）。"""
    user = await db.get(User, user_id)
    if not user:
        return error_response("E1006", "用户不存在")
    if is_disabled is not None:
        user.is_disabled = is_disabled
    if role is not None:
        user.role = role
    if persona_type is not None:
        user.persona_type = persona_type
    await db.commit()
    await db.refresh(user)
    return success_response(data={"id": user.id, "is_disabled": user.is_disabled, "role": user.role}, message="已更新")


# === 美食内容管理 ===
@router.post("/foods")
async def create_food(
    category_id: int = Form(...),
    name: str = Form(..., min_length=2, max_length=100),
    type: str = Form("dish"),
    description: str = Form(""),
    image: UploadFile | None = File(None),
    address: str = Form(""),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    price_range: str = Form(""),
    tags: str = Form("[]"),
    is_recommended: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """新增美食。"""
    try:
        tags_list = json.loads(tags) if tags else []
    except json.JSONDecodeError:
        tags_list = []

    # 处理图片上传
    image_url = ""
    if image and image.filename:
        import os, uuid
        from config import get_settings
        settings = get_settings()
        ext = os.path.splitext(image.filename)[1] or ".jpg"
        filename = f"food_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(settings.UPLOAD_DIR, filename)
        content = await image.read()
        with open(filepath, "wb") as f:
            f.write(content)
        image_url = f"/uploads/{filename}"

    food = Food(
        category_id=category_id, name=name, type=type,
        description=description, image_url=image_url,
        address=address, latitude=latitude, longitude=longitude,
        price_range=price_range, tags=tags_list, is_recommended=is_recommended,
    )
    db.add(food)
    await db.commit()
    await db.refresh(food)
    return success_response(data={"id": food.id, "name": food.name}, message="已创建")


@router.put("/foods/{food_id}")
async def update_food(
    food_id: int,
    category_id: int | None = Form(None),
    name: str | None = Form(None),
    type: str | None = Form(None),
    description: str | None = Form(None),
    image: UploadFile | None = File(None),
    address: str | None = Form(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    price_range: str | None = Form(None),
    tags: str | None = Form(None),
    is_recommended: bool | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """编辑美食。"""
    food = await db.get(Food, food_id)
    if not food:
        return error_response("E1006", "美食不存在")

    if category_id is not None:
        food.category_id = category_id
    if name is not None:
        food.name = name
    if type is not None:
        food.type = type
    if description is not None:
        food.description = description
    if address is not None:
        food.address = address
    if latitude is not None:
        food.latitude = latitude
    if longitude is not None:
        food.longitude = longitude
    if price_range is not None:
        food.price_range = price_range
    if tags is not None:
        try:
            food.tags = json.loads(tags)
        except json.JSONDecodeError:
            pass
    if is_recommended is not None:
        food.is_recommended = is_recommended

    # 处理图片上传
    if image and image.filename:
        import os, uuid
        from config import get_settings
        settings = get_settings()
        ext = os.path.splitext(image.filename)[1] or ".jpg"
        filename = f"food_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(settings.UPLOAD_DIR, filename)
        content = await image.read()
        with open(filepath, "wb") as f:
            f.write(content)
        food.image_url = f"/uploads/{filename}"

    await db.commit()
    await db.refresh(food)
    return success_response(data={"id": food.id, "name": food.name}, message="已更新")


@router.delete("/foods/{food_id}")
async def delete_food(
    food_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """删除美食。"""
    food = await db.get(Food, food_id)
    if not food:
        return error_response("E1006", "美食不存在")
    await db.delete(food)
    await db.commit()
    return success_response(message="已删除")


# === 非遗内容管理 ===
@router.post("/heritages")
async def create_heritage(
    name: str = Form(..., min_length=2, max_length=100),
    category: str = Form(..., description="国家级/省级/市级"),
    type: str = Form(..., description="传统戏剧/传统技艺/民俗/传统舞蹈/传统美术/传统音乐"),
    description: str = Form(""),
    image: UploadFile | None = File(None),
    video_url: str = Form(""),
    inheritor: str = Form(""),
    region: str = Form(..., description="汕头/潮州/揭阳/汕尾"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """新增非遗项目。"""
    image_url = ""
    if image and image.filename:
        import os, uuid
        from config import get_settings
        settings = get_settings()
        ext = os.path.splitext(image.filename)[1] or ".jpg"
        filename = f"heritage_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(settings.UPLOAD_DIR, filename)
        content = await image.read()
        with open(filepath, "wb") as f:
            f.write(content)
        image_url = f"/uploads/{filename}"

    heritage = Heritage(
        name=name, category=category, type=type,
        description=description, image_url=image_url,
        video_url=video_url, inheritor=inheritor, region=region,
    )
    db.add(heritage)
    await db.commit()
    await db.refresh(heritage)
    return success_response(data={"id": heritage.id, "name": heritage.name}, message="已创建")


@router.put("/heritages/{heritage_id}")
async def update_heritage(
    heritage_id: int,
    name: str | None = Form(None),
    category: str | None = Form(None),
    type: str | None = Form(None),
    description: str | None = Form(None),
    image: UploadFile | None = File(None),
    video_url: str | None = Form(None),
    inheritor: str | None = Form(None),
    region: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """编辑非遗项目。"""
    heritage = await db.get(Heritage, heritage_id)
    if not heritage:
        return error_response("E1006", "非遗项目不存在")

    if name is not None:
        heritage.name = name
    if category is not None:
        heritage.category = category
    if type is not None:
        heritage.type = type
    if description is not None:
        heritage.description = description
    if video_url is not None:
        heritage.video_url = video_url
    if inheritor is not None:
        heritage.inheritor = inheritor
    if region is not None:
        heritage.region = region

    if image and image.filename:
        import os, uuid
        from config import get_settings
        settings = get_settings()
        ext = os.path.splitext(image.filename)[1] or ".jpg"
        filename = f"heritage_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(settings.UPLOAD_DIR, filename)
        content = await image.read()
        with open(filepath, "wb") as f:
            f.write(content)
        heritage.image_url = f"/uploads/{filename}"

    await db.commit()
    await db.refresh(heritage)
    return success_response(data={"id": heritage.id, "name": heritage.name}, message="已更新")


@router.delete("/heritages/{heritage_id}")
async def delete_heritage(
    heritage_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """删除非遗项目。"""
    heritage = await db.get(Heritage, heritage_id)
    if not heritage:
        return error_response("E1006", "非遗项目不存在")
    await db.delete(heritage)
    await db.commit()
    return success_response(message="已删除")


# === 社区审核 ===
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
@router.get("/posts")
async def list_posts_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    post_type: str = Query(""),
    keyword: str = Query(""),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    q = select(CommunityPost)
    if post_type:
        q = q.where(CommunityPost.post_type == post_type)
    if keyword:
        q = q.where(CommunityPost.title.contains(keyword) | CommunityPost.content.contains(keyword))

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(
        q.order_by(CommunityPost.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

<<<<<<< HEAD
    return paginated(
        items=[
=======
    return success_response(data={
        "items": [
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
            {
                "id": p.id, "title": p.title, "content": p.content[:100] if p.content else "",
                "post_type": p.post_type, "like_count": p.like_count,
                "comment_count": p.comment_count, "view_count": p.view_count,
                "tags": p.tags, "created_at": str(p.created_at),
            }
            for p in rows
        ],
<<<<<<< HEAD
        total=total, page=page, page_size=page_size,
    )
=======
        "total": total,
    })
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22


@router.get("/posts/{post_id}")
async def get_post_detail_admin(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
<<<<<<< HEAD
    post = await db.get(CommunityPost, post_id)
    if not post:
        raise HTTPException(404, detail="帖子不存在")
    return success(data={
=======
    """查看帖子详情（含完整内容）。"""
    post = await db.get(CommunityPost, post_id)
    if not post:
        return error_response("E1006", "帖子不存在")
    return success_response(data={
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
        "id": post.id, "title": post.title, "content": post.content,
        "images": post.images, "tags": post.tags, "post_type": post.post_type,
        "view_count": post.view_count, "like_count": post.like_count,
        "comment_count": post.comment_count, "created_at": str(post.created_at),
    })


@router.delete("/posts/{post_id}")
async def delete_post_admin(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
<<<<<<< HEAD
    post = await db.get(CommunityPost, post_id)
    if not post:
        raise HTTPException(404, detail="帖子不存在")

    from models.community import PostLike
=======
    """删除帖子（管理员可删任何人）。"""
    post = await db.get(CommunityPost, post_id)
    if not post:
        return error_response("E1006", "帖子不存在")
    # 同时删除关联评论和点赞
    from models.community import PostLike
    await db.execute(select(PostComment).where(PostComment.post_id == post_id))
    await db.execute(select(PostLike).where(PostLike.post_id == post_id))
    # 使用 ORM 批量删除，避免 SQL 注入
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    comments = (await db.execute(
        select(PostComment).where(PostComment.post_id == post_id)
    )).scalars().all()
    likes = (await db.execute(
        select(PostLike).where(PostLike.post_id == post_id)
    )).scalars().all()
    for c in comments:
        await db.delete(c)
    for l in likes:
        await db.delete(l)
    await db.delete(post)
    await db.commit()
<<<<<<< HEAD
    return success(message="已删除")
=======
    return success_response(message="已删除")
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22


@router.delete("/comments/{comment_id}")
async def delete_comment_admin(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
<<<<<<< HEAD
    comment = await db.get(PostComment, comment_id)
    if not comment:
        raise HTTPException(404, detail="评论不存在")
    await db.delete(comment)
    await db.commit()
    return success(message="已删除")


# ─────────────────────────────────────────────────────────
# 数据管理
# ─────────────────────────────────────────────────────────

=======
    """删除评论。"""
    comment = await db.get(PostComment, comment_id)
    if not comment:
        return error_response("E1006", "评论不存在")
    await db.delete(comment)
    await db.commit()
    return success_response(message="已删除")


# === 数据管理 ===
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
@router.get("/weather-logs")
async def get_weather_logs(
    page: int = Query(1), page_size: int = Query(20),
    region: str = Query(""),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    q = select(WeatherRecord).order_by(WeatherRecord.record_time.desc())
    if region:
        q = q.where(WeatherRecord.region == region)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
<<<<<<< HEAD
    return paginated(
        items=[
=======
    return success_response(data={
        "items": [
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
            {
                "id": r.id, "region": r.region, "temperature": float(r.temperature),
                "humidity": r.humidity, "weather_desc": r.weather_desc,
                "wind_level": r.wind_level, "record_time": str(r.record_time),
            }
            for r in rows
        ],
<<<<<<< HEAD
        total=total, page=page, page_size=page_size,
    )
=======
        "total": total,
    })
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22


@router.get("/crowd-logs")
async def get_crowd_logs(
    page: int = Query(1), page_size: int = Query(20),
    region: str = Query(""),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    q = select(CrowdRecord).order_by(CrowdRecord.record_time.desc())
    if region:
        q = q.where(CrowdRecord.region == region)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
<<<<<<< HEAD
    return paginated(
        items=[
=======
    return success_response(data={
        "items": [
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
            {
                "id": r.id, "region": r.region, "location_name": r.location_name,
                "crowd_level": r.crowd_level, "estimated_count": r.estimated_count,
                "record_time": str(r.record_time),
            }
            for r in rows
        ],
<<<<<<< HEAD
        total=total, page=page, page_size=page_size,
    )
=======
        "total": total,
    })
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22


@router.post("/refresh-weather")
async def refresh_weather(current_user=Depends(require_admin)):
<<<<<<< HEAD
    try:
        from utils.weather_fetcher import fetch_weather_data
        await fetch_weather_data()
        return success(message="气象数据刷新成功")
    except Exception as e:
        raise HTTPException(500, detail=f"气象数据拉取失败: {str(e)}")
=======
    """手动触发气象数据拉取。"""
    try:
        from utils.weather_fetcher import fetch_weather_data
        await fetch_weather_data()
        return success_response(message="气象数据刷新成功")
    except Exception as e:
        return error_response("E2001", f"气象数据拉取失败: {str(e)}")
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22


@router.post("/generate-crowd")
async def generate_crowd(current_user=Depends(require_admin)):
<<<<<<< HEAD
    try:
        from utils.weather_fetcher import generate_crowd_data
        await generate_crowd_data()
        return success(message="人流模拟数据已生成")
    except Exception as e:
        raise HTTPException(500, detail=f"人流数据生成失败: {str(e)}")


# ─────────────────────────────────────────────────────────
# 系统设置
# ─────────────────────────────────────────────────────────

def _read_env_file() -> dict[str, str]:
    """读取 .env 文件为键值对字典。"""
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".env",
    )
    result = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _write_env_file(updates: dict[str, str]):
    """将更新写入 .env 文件，保留原有注释和未修改的键。"""
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".env",
    )
    if not os.path.exists(env_path):
        # 新建 .env
        with open(env_path, "w", encoding="utf-8") as f:
            for key, value in updates.items():
                if value:
                    f.write(f"{key}={value}\n")
        return

    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_keys = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line.rstrip("\n"))
            continue
        if "=" in stripped:
            key = stripped.partition("=")[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}")
                updated_keys.add(key)
            else:
                new_lines.append(line.rstrip("\n"))
        else:
            new_lines.append(line.rstrip("\n"))

    # 追加新增的键
    for key, value in updates.items():
        if key not in updated_keys and value:
            new_lines.append(f"{key}={value}")

    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")


@router.get("/settings")
async def get_settings(current_user=Depends(require_admin)):
    env = _read_env_file()
    api_key = env.get("LLM_API_KEY", "") or env.get("QWEN_API_KEY", "") or env.get("DEEPSEEK_API_KEY", "")
    return success(data={
        # LLM
        "llm_provider": env.get("LLM_PROVIDER", "qwen"),
        "llm_model": env.get("QWEN_MODEL", "") or env.get("DEEPSEEK_MODEL", "qwen-turbo"),
        "api_key": ("****" + api_key[-4:]) if len(api_key) > 4 else ("****" if api_key else ""),
        # SMTP
        "smtp_server": env.get("SMTP_SERVER", "smtp.163.com"),
        "smtp_username": env.get("SMTP_USERNAME", ""),
        "smtp_password": ("****" + env["SMTP_PASSWORD"][-2:]) if len(env.get("SMTP_PASSWORD", "")) > 2 else "",
        "smtp_from": env.get("SMTP_FROM", ""),
        # 短信
        "sms_access_key": env.get("SMS_ACCESS_KEY", ""),
        "sms_access_secret": ("******") if env.get("SMS_ACCESS_SECRET") else "",
        "sms_sign_name": env.get("SMS_SIGN_NAME", "潮汕文化平台"),
        # 天气
        "weather_api_key": env.get("QWEATHER_API_KEY", ""),
=======
    """手动触发人流模拟数据生成。"""
    try:
        from utils.weather_fetcher import generate_crowd_data
        await generate_crowd_data()
        return success_response(message="人流模拟数据已生成")
    except Exception as e:
        return error_response("E2001", f"人流数据生成失败: {str(e)}")


# === 系统设置 ===
@router.get("/settings")
async def get_settings(current_user=Depends(require_admin)):
    import os
    return success_response(data={
        "llm_provider": os.getenv("LLM_PROVIDER", "qwen"),
        "llm_model": os.getenv("QWEN_MODEL", "") or os.getenv("DEEPSEEK_MODEL", "qwen-turbo"),
        "api_key": "***",
        "smtp_server": os.getenv("SMTP_SERVER", "smtp.163.com"),
        "smtp_username": os.getenv("SMTP_USERNAME", ""),
        "smtp_from": os.getenv("SMTP_FROM", ""),
        "weather_api_key": os.getenv("QWEATHER_API_KEY", ""),
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    })


@router.put("/settings")
<<<<<<< HEAD
async def update_settings(
    body: SettingsAdminUpdate,
    current_user=Depends(require_admin),
):
    """更新 .env 中的系统配置。"""
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, detail="没有需要更新的字段")

    # 映射前端字段 → .env 键
    key_map = {
        "llm_provider": "LLM_PROVIDER",
        "llm_model": "QWEN_MODEL",
        "api_key": "LLM_API_KEY",
        "smtp_server": "SMTP_SERVER",
        "smtp_username": "SMTP_USERNAME",
        "smtp_password": "SMTP_PASSWORD",
        "smtp_from": "SMTP_FROM",
        "sms_access_key": "SMS_ACCESS_KEY",
        "sms_access_secret": "SMS_ACCESS_SECRET",
        "sms_sign_name": "SMS_SIGN_NAME",
        "weather_api_key": "QWEATHER_API_KEY",
    }

    env_updates = {}
    for field, env_key in key_map.items():
        if field in update_data and update_data[field] is not None:
            env_updates[env_key] = update_data[field]

    if env_updates:
        _write_env_file(env_updates)

    return success(message="设置已保存，部分配置需重启服务生效")
=======
async def update_settings(current_user=Depends(require_admin)):
    return success_response(message="设置已更新（需在 .env 文件中手动修改后重启服务生效）")
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
