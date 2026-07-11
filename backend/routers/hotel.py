"""酒店 API 路由"""

from fastapi import APIRouter, Query
from sqlalchemy import select, func as sqlfunc

from database import async_session_factory
from models.hotel import Hotel
from schemas.hotel import HotelOut, HotelListParams
from utils.geo import haversine

router = APIRouter(prefix="/hotels", tags=["hotels"])


@router.get("")
async def list_hotels(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    region: str | None = None,
    stars: int | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    keyword: str | None = None,
    is_recommended: bool | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = Query(None, ge=0.5, le=50),
):
    """酒店列表（支持区域/星级/价格筛选 + 坐标范围查询）"""
    async with async_session_factory() as db:
        stmt = select(Hotel)

        if region:
            stmt = stmt.where(Hotel.region == region)
        if stars is not None:
            stmt = stmt.where(Hotel.stars == stars)
        if price_min is not None:
            stmt = stmt.where(Hotel.price_max >= price_min)
        if price_max is not None:
            stmt = stmt.where(Hotel.price_min <= price_max)
        if keyword:
            stmt = stmt.where(Hotel.name.contains(keyword))
        if is_recommended is not None:
            stmt = stmt.where(Hotel.is_recommended == is_recommended)

        # 坐标范围查询：先用 region 粗筛，再在 Python 中精确计算距离
        if lat is not None and lng is not None and radius_km:
            if not region:
                # 无 region 时不做粗筛，直接全表计算（数据量小可接受）
                pass

        # 总数
        count_q = select(sqlfunc.count()).select_from(stmt.subquery())
        total = (await db.execute(count_q)).scalar()

        # 分页
        offset = (page - 1) * page_size
        rows = (await db.execute(stmt.offset(offset).limit(page_size))).scalars().all()

        items = []
        for h in rows:
            item = HotelOut.model_validate(h).model_dump()
            # 计算距离
            if lat is not None and lng is not None and h.latitude and h.longitude:
                item["distance_km"] = round(
                    haversine(lat, lng, float(h.latitude), float(h.longitude)), 2
                )
                # 按半径过滤
                if radius_km and item["distance_km"] > radius_km:
                    continue
            items.append(item)

        return {
            "code": 0,
            "message": "ok",
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            },
        }


@router.get("/{hotel_id}")
async def get_hotel(hotel_id: int):
    """酒店详情"""
    async with async_session_factory() as db:
        hotel = await db.get(Hotel, hotel_id)
        if not hotel:
            return {"code": 1, "message": "酒店不存在", "data": None}
        return {
            "code": 0,
            "message": "ok",
            "data": HotelOut.model_validate(hotel).model_dump(),
        }
