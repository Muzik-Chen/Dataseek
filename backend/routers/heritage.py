"""
非遗 & 民俗活动路由。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.heritage import Heritage
from schemas.heritage import HeritageOut
from utils.response import success, paginated

router = APIRouter(tags=["非遗与民俗"])


# ===== 非遗 =====
@router.get("/heritages")
async def list_heritages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    type: str | None = None,
    region: str | None = None,
    keyword: str | None = None,
    is_recommended: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Heritage)
    count_q = select(func.count(Heritage.id))

    if category:
        q = q.where(Heritage.category == category)
        count_q = count_q.where(Heritage.category == category)
    if type:
        q = q.where(Heritage.type == type)
        count_q = count_q.where(Heritage.type == type)
    if region:
        q = q.where(Heritage.region == region)
        count_q = count_q.where(Heritage.region == region)
    if keyword:
        q = q.where(Heritage.name.contains(keyword))
        count_q = count_q.where(Heritage.name.contains(keyword))

    q = q.order_by(Heritage.view_count.desc())
    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)

    total = (await db.execute(count_q)).scalar()
    rows = (await db.execute(q)).scalars().all()
    items = [HeritageOut.model_validate(r).model_dump() for r in rows]
    return paginated(items, total, page, page_size)


@router.get("/heritages/{heritage_id}")
async def get_heritage(heritage_id: int, db: AsyncSession = Depends(get_db)):
    h = (await db.execute(select(Heritage).where(Heritage.id == heritage_id))).scalar()
    if not h:
        raise HTTPException(status_code=404, detail="非遗项目不存在")
    h.view_count += 1
    await db.flush()
    return success(HeritageOut.model_validate(h).model_dump())


# ===== 民俗活动路由已迁移至 routers/festival.py =====
# 请使用 /api/v1/events 和 /api/v1/admin/events 系列接口
