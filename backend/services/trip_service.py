"""
行程规划业务逻辑 — AI 生成 + CRUD。
"""
import json
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.trip import TripPlan


async def create_trip_plan(
    db: AsyncSession,
    user_id: int,
    title: str,
    days: int,
    crowd_type: str,
    preferences: dict,
) -> TripPlan:
    """AI 生成行程方案并保存到数据库。plan_content 由调用方注入。"""
    plan = TripPlan(
        user_id=user_id,
        title=title,
        days=days,
        crowd_type=crowd_type,
        preferences=preferences,
        plan_content={},  # 占位，由 router 层调用 AI 后填充
        status="generated",
    )
    db.add(plan)
    await db.flush()
    return plan


async def save_trip_content(
    db: AsyncSession, plan: TripPlan, plan_content: dict,
) -> TripPlan:
    """保存 AI 生成的行程内容。"""
    plan.plan_content = plan_content
    plan.status = "generated"
    await db.flush()
    return plan


async def get_user_trips(
    db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10,
) -> tuple[list[TripPlan], int]:
    """获取用户的历史行程列表。"""
    from sqlalchemy import func
    q = select(TripPlan).where(TripPlan.user_id == user_id).order_by(desc(TripPlan.created_at))
    count_q = select(func.count(TripPlan.id)).where(TripPlan.user_id == user_id)

    total = (await db.execute(count_q)).scalar()
    offset = (page - 1) * page_size
    rows = (await db.execute(q.offset(offset).limit(page_size))).scalars().all()
    return list(rows), total


async def get_trip_detail(
    db: AsyncSession, trip_id: int, user_id: int,
) -> TripPlan:
    """获取行程详情（校验归属）。"""
    plan = (await db.execute(
        select(TripPlan).where(TripPlan.id == trip_id)
    )).scalar()
    if not plan:
        raise ValueError("行程不存在")
    if plan.user_id != user_id:
        raise PermissionError("无权访问此行程")
    return plan


async def delete_trip(
    db: AsyncSession, trip_id: int, user_id: int,
) -> None:
    """删除行程（校验归属）。"""
    plan = await get_trip_detail(db, trip_id, user_id)
    await db.delete(plan)
    await db.flush()
