"""
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

from models.user import User
from models.food import Food, FoodCategory
from models.heritage import Heritage
from models.community import CommunityPost, PostComment
from models.dashboard import WeatherRecord, CrowdRecord
from models.chat import ChatMessage
from models.favorite import UserFavorite
from models.trip import TripPlan
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
    total_events = (await db.execute(select(func.count(FolkEvent.id)))).scalar()

    # ai_calls_today — 从 chat_messages 按当天统计
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    ai_calls_today = (await db.execute(
        select(func.count(ChatMessage.id)).where(
            func.date(ChatMessage.created_at) == today
        )
    )).scalar()

    # 近7天新增用户趋势
    new_users_7d = (await db.execute(
        text("SELECT DATE(created_at) as d, COUNT(*) as c FROM users WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) GROUP BY d ORDER BY d")
    )).fetchall()
    active_posts_7d = (await db.execute(
        text("SELECT DATE(created_at) as d, COUNT(*) as c FROM community_posts WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) GROUP BY d ORDER BY d")
    )).fetchall()

    return success(data={
        "total_users": total_users,
        "total_foods": total_foods,
        "total_heritages": total_heritages,
        "total_posts": total_posts,
        "total_events": total_events,
        "ai_calls_today": ai_calls_today or 0,
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

    return success(data={
        "posts": [{"id": p.id, "title": p.title, "post_type": p.post_type, "created_at": str(p.created_at)} for p in posts],
        "chat_messages": [{"id": m.id, "content": m.content[:50] if m.content else "", "role": m.role, "created_at": str(m.created_at)} for m in msgs],
    })


# ─────────────────────────────────────────────────────────
# 用户管理
# ─────────────────────────────────────────────────────────

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

    return paginated(
        items=[
            {
                "id": u.id, "email": mask_email(u.email), "phone": u.phone,
                "nickname": u.nickname,
                "persona_type": u.persona_type, "role": u.role,
                "is_disabled": u.is_disabled, "created_at": str(u.created_at),
            }
            for u in rows
        ],
        total=total, page=page, page_size=page_size,
    )


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """用户详情（含收藏数+行程数+动态数）。"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, detail="用户不存在")

    fav_count = (await db.execute(
        select(func.count()).select_from(UserFavorite).where(UserFavorite.user_id == user_id)
    )).scalar()
    trip_count = (await db.execute(
        select(func.count()).select_from(TripPlan).where(TripPlan.user_id == user_id)
    )).scalar()
    post_count = (await db.execute(
        select(func.count()).select_from(CommunityPost).where(CommunityPost.user_id == user_id)
    )).scalar()

    return success(data={
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

    return paginated(
        items=[
            {
                "id": p.id, "title": p.title, "content": p.content[:100] if p.content else "",
                "post_type": p.post_type, "like_count": p.like_count,
                "comment_count": p.comment_count, "view_count": p.view_count,
                "tags": p.tags, "created_at": str(p.created_at),
            }
            for p in rows
        ],
        total=total, page=page, page_size=page_size,
    )


@router.get("/posts/{post_id}")
async def get_post_detail_admin(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    post = await db.get(CommunityPost, post_id)
    if not post:
        raise HTTPException(404, detail="帖子不存在")
    return success(data={
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
    post = await db.get(CommunityPost, post_id)
    if not post:
        raise HTTPException(404, detail="帖子不存在")

    from models.community import PostLike
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
    return success(message="已删除")


@router.delete("/comments/{comment_id}")
async def delete_comment_admin(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    comment = await db.get(PostComment, comment_id)
    if not comment:
        raise HTTPException(404, detail="评论不存在")
    await db.delete(comment)
    await db.commit()
    return success(message="已删除")


# ─────────────────────────────────────────────────────────
# 数据管理
# ─────────────────────────────────────────────────────────

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
    return paginated(
        items=[
            {
                "id": r.id, "region": r.region, "temperature": float(r.temperature),
                "humidity": r.humidity, "weather_desc": r.weather_desc,
                "wind_level": r.wind_level, "record_time": str(r.record_time),
            }
            for r in rows
        ],
        total=total, page=page, page_size=page_size,
    )


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
    return paginated(
        items=[
            {
                "id": r.id, "region": r.region, "location_name": r.location_name,
                "crowd_level": r.crowd_level, "estimated_count": r.estimated_count,
                "record_time": str(r.record_time),
            }
            for r in rows
        ],
        total=total, page=page, page_size=page_size,
    )


@router.post("/refresh-weather")
async def refresh_weather(current_user=Depends(require_admin)):
    try:
        from utils.weather_fetcher import fetch_weather_data
        await fetch_weather_data()
        return success(message="气象数据刷新成功")
    except Exception as e:
        raise HTTPException(500, detail=f"气象数据拉取失败: {str(e)}")


@router.post("/generate-crowd")
async def generate_crowd(current_user=Depends(require_admin)):
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
    })


@router.put("/settings")
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
