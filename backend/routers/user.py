"""
用户模块路由 — 个人中心/收藏/偏好。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from models.favorite import UserFavorite
from models.food import Food
from models.heritage import Heritage, FolkEvent
from schemas.user import (
    UserOut, UserProfileUpdate, ChangePasswordRequest,
    FavoriteOut, FavoriteCreate,
)
from utils.security import hash_password, verify_password
from utils.response import success, paginated
from utils.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["用户"])


# ===== 个人资料 =====
@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户的个人信息。"""
    return success(UserOut.model_validate(current_user).model_dump())


@router.put("/profile")
async def update_profile(
    req: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新个人信息。"""
    update_data = req.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(current_user, key, val)
    await db.flush()
    return success(UserOut.model_validate(current_user).model_dump(), "更新成功")


@router.put("/password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码。"""
    if not verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_user.password_hash = hash_password(req.new_password)
    await db.flush()
    return success(message="密码修改成功")


# ===== 收藏 =====
@router.get("/favorites")
async def list_favorites(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    item_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的收藏列表。"""
    user_id = current_user.id
    q = select(UserFavorite).where(UserFavorite.user_id == user_id)
    count_q = select(func.count(UserFavorite.id)).where(UserFavorite.user_id == user_id)

    if item_type:
        q = q.where(UserFavorite.item_type == item_type)
        count_q = count_q.where(UserFavorite.item_type == item_type)

    q = q.order_by(UserFavorite.created_at.desc())
    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)

    total = (await db.execute(count_q)).scalar()
    rows = (await db.execute(q)).scalars().all()

    # 批量查询关联数据
    items = []
    food_ids = [r.item_id for r in rows if r.item_type == "food"]
    heritage_ids = [r.item_id for r in rows if r.item_type == "heritage"]
    event_ids = [r.item_id for r in rows if r.item_type == "event"]

    food_map = {}
    if food_ids:
        foods = (await db.execute(select(Food).where(Food.id.in_(food_ids)))).scalars().all()
        food_map = {f.id: {"name": f.name, "image_url": f.image_url, "type": f.type} for f in foods}

    heritage_map = {}
    if heritage_ids:
        heritages = (await db.execute(select(Heritage).where(Heritage.id.in_(heritage_ids)))).scalars().all()
        heritage_map = {h.id: {"name": h.name, "image_url": h.image_url, "type": h.type} for h in heritages}

    event_map = {}
    if event_ids:
        events = (await db.execute(select(FolkEvent).where(FolkEvent.id.in_(event_ids)))).scalars().all()
        event_map = {e.id: {"name": e.name, "image_url": e.image_url, "event_date": str(e.event_date)} for e in events}

    for r in rows:
        fav = FavoriteOut.model_validate(r).model_dump()
        if r.item_type == "food":
            fav["detail"] = food_map.get(r.item_id)
        elif r.item_type == "heritage":
            fav["detail"] = heritage_map.get(r.item_id)
        elif r.item_type == "event":
            fav["detail"] = event_map.get(r.item_id)
        items.append(fav)

    return paginated(items, total, page, page_size)


@router.post("/favorites")
async def add_favorite(
    req: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """添加收藏。"""
    user_id = current_user.id
    existing = (await db.execute(
        select(UserFavorite).where(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.item_type == req.item_type,
                UserFavorite.item_id == req.item_id,
            )
        )
    )).scalar()
    if existing:
        raise HTTPException(status_code=400, detail="已收藏")

    fav = UserFavorite(user_id=user_id, item_type=req.item_type, item_id=req.item_id)
    db.add(fav)
    await db.flush()
<<<<<<< HEAD
    await db.refresh(fav)  # 加载 server_default 生成的 created_at，避免 MissingGreenlet
    return success(FavoriteOut.model_validate(fav).model_dump(), "收藏成功")


@router.get("/favorites/check")
async def check_favorite(
    item_type: str = Query(..., description="类型: food/heritage/event"),
    item_id: int = Query(..., description="项目ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """检查当前用户是否已收藏某个项目，返回收藏状态和收藏记录ID。"""
    fav = (await db.execute(
        select(UserFavorite).where(
            and_(
                UserFavorite.user_id == current_user.id,
                UserFavorite.item_type == item_type,
                UserFavorite.item_id == item_id,
            )
        )
    )).scalar()
    return success({
        "is_favorited": fav is not None,
        "favorite_id": fav.id if fav else None,
    })


=======
    return success(FavoriteOut.model_validate(fav).model_dump(), "收藏成功")


>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
@router.delete("/favorites/{favorite_id}")
async def remove_favorite(
    favorite_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消收藏。"""
    fav = (await db.execute(
        select(UserFavorite).where(
            and_(UserFavorite.id == favorite_id, UserFavorite.user_id == current_user.id)
        )
    )).scalar()
    if not fav:
        raise HTTPException(status_code=404, detail="收藏不存在")
    await db.delete(fav)
    await db.flush()
    return success(message="已取消收藏")
