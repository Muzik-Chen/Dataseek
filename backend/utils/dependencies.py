"""
FastAPI 通用依赖注入 — JWT 认证、分页参数。
"""
from fastapi import Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from utils.security import decode_access_token


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 Authorization Header 中解析 JWT 并返回当前用户。

    用法:
        @router.get("/profile")
        async def profile(user: User = Depends(get_current_user)):
            ...
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="请先登录")

    # 支持 "Bearer <token>" 和直接 "<token>" 两种格式
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token 无效")

    user = (await db.execute(select(User).where(User.id == user_id))).scalar()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if user.is_disabled:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    return user


async def get_optional_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """可选认证 — 未登录时返回 None 而非 401。

    用于需要感知登录状态但不对未登录用户设限的接口。
    """
    if not authorization:
        return None
    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None


async def get_admin_user(
    user: User = Depends(get_current_user),
) -> User:
    """仅管理员可访问。"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# 别名 — 部分 router 使用了 require_admin 这个名称
require_admin = get_admin_user
