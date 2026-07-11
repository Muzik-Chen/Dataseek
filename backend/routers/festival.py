"""
节日/民俗活动路由 — 前台浏览（后台管理移至 AdminResource 工厂）。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from database import get_db
from utils.response import success_response, error_response
from models.heritage import FolkEvent

router = APIRouter(tags=["民俗活动"])


# ===== 前台接口 =====

@router.get("/events")
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: str = Query(""),
    region: str = Query(""),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    keyword: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """民俗活动/节日列表（分页+筛选）。"""
    q = select(FolkEvent)

    if event_type:
        q = q.where(FolkEvent.event_type == event_type)
    if region:
        q = q.where(FolkEvent.region == region)
    if date_from:
        q = q.where(FolkEvent.event_date >= date_from)
    if date_to:
        q = q.where(FolkEvent.event_date <= date_to)
    if keyword:
        q = q.where(
            FolkEvent.name.contains(keyword) |
            FolkEvent.description.contains(keyword)
        )

    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar()

    rows = (await db.execute(
        q.order_by(FolkEvent.event_date.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    return success_response(data={
        "items": [
            {
                "id": e.id,
                "name": e.name,
                "description": e.description,
                "event_date": str(e.event_date) if e.event_date else None,
                "lunar_date": e.lunar_date,
                "region": e.region,
                "latitude": float(e.latitude) if e.latitude else None,
                "longitude": float(e.longitude) if e.longitude else None,
                "address": e.address or "",
                "image_url": e.image_url,
                "event_type": e.event_type,
                "created_at": str(e.created_at) if e.created_at else None,
            }
            for e in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/events/{event_id}")
async def get_event_detail(
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    """活动/节日详情。"""
    event = await db.get(FolkEvent, event_id)
    if not event:
        return error_response("E1006", "活动不存在")
    return success_response(data={
        "id": event.id,
        "name": event.name,
        "description": event.description,
        "event_date": str(event.event_date) if event.event_date else None,
        "lunar_date": event.lunar_date,
        "region": event.region,
        "latitude": float(event.latitude) if event.latitude else None,
        "longitude": float(event.longitude) if event.longitude else None,
        "address": event.address or "",
        "image_url": event.image_url,
        "event_type": event.event_type,
        "created_at": str(event.created_at) if event.created_at else None,
    })
