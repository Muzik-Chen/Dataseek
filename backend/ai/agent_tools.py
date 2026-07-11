"""
Agent Tools — LangChain Tool 集合，供 Food Agent 和 Hotel Agent 调用。

所有 tool 直接查询 MySQL 数据库（通过 async_session_factory），
返回结构化 JSON 供 LLM 推理使用。

Food tools (3):
    search_foods_by_location — 按坐标+半径搜索周边美食
    search_foods_by_type     — 按类型关键词搜索（牛肉火锅/海鲜/小吃…）
    get_food_detail          — 按 ID 获取单条美食详情

Hotel tools (3):
    search_hotels_by_location — 按坐标+半径搜索周边酒店
    search_hotels_by_stars    — 按星级范围筛选
    get_hotel_detail          — 按 ID 获取单条酒店详情
"""
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy import select

from database import async_session_factory
from models.food import Food
from models.hotel import Hotel
from utils.geo import haversine


# ═══════════════════════════════════════════
# Food Tools (3)
# ═══════════════════════════════════════════

@tool
async def search_foods_by_location(
    lat: float,
    lng: float,
    radius_km: float = 3.0,
    limit: int = 10,
) -> list[dict]:
    """搜索指定坐标周边的美食餐厅。

    参数：
        lat: 纬度 (如 23.357)
        lng: 经度 (如 116.672)
        radius_km: 搜索半径(公里)，默认 3.0
        limit: 最多返回条数，默认 10

    返回：周边美食列表，含 food_id/name/type/price_range/distance_km/tags
    """
    async with async_session_factory() as db:
        result = await db.execute(
            select(Food).where(
                Food.latitude.isnot(None),
                Food.longitude.isnot(None),
            )
        )
        foods = result.scalars().all()

    nearby = []
    for f in foods:
        d = haversine(lat, lng, float(f.latitude), float(f.longitude))
        if d <= radius_km:
            tags = f.tags if isinstance(f.tags, list) else []
            nearby.append({
                "food_id": f.id,
                "name": f.name,
                "type": f.type,
                "price_range": f.price_range or "",
                "distance_km": round(d, 2),
                "tags": tags,
                "address": f.address or "",
            })

    nearby.sort(key=lambda x: x["distance_km"])
    return nearby[:limit]


@tool
async def search_foods_by_type(
    type_keyword: str,
    limit: int = 10,
) -> list[dict]:
    """按美食类型搜索餐厅。

    参数：
        type_keyword: 类型关键词，如 '牛肉火锅'、'海鲜'、'粿条'、'小吃'、'甜品'
        limit: 最多返回条数，默认 10

    返回：匹配的美食列表，含 food_id/name/type/price_range/address/tags
    """
    async with async_session_factory() as db:
        # 搜索 name/type 字段包含关键词
        from sqlalchemy import or_

        result = await db.execute(
            select(Food).where(
                or_(
                    Food.name.contains(type_keyword),
                    Food.type.contains(type_keyword),
                    Food.description.contains(type_keyword),
                )
            ).limit(limit * 2)  # 多取一些，再过滤 tags
        )
        candidates = result.scalars().all()

    items = []
    for f in candidates:
        tags = f.tags if isinstance(f.tags, list) else []
        # tags 也参与匹配（JSON 数组字段）
        tag_match = any(type_keyword in (t or "") for t in tags)
        name_match = type_keyword in (f.name or "")
        type_match = type_keyword in (f.type or "")

        if name_match or type_match or tag_match:
            items.append({
                "food_id": f.id,
                "name": f.name,
                "type": f.type,
                "price_range": f.price_range or "",
                "address": f.address or "",
                "tags": tags,
                "image_url": f.image_url or "",
                "lat": float(f.latitude) if f.latitude else None,
                "lng": float(f.longitude) if f.longitude else None,
            })

    # 优先返回有坐标的
    items.sort(key=lambda x: (0 if x["lat"] else 1, x["name"]))
    return items[:limit]


@tool
async def get_food_detail(food_id: int) -> Optional[dict]:
    """获取单条美食的详细信息。

    参数：
        food_id: 美食 ID

    返回：美食详情，含 name/type/description/price_range/image_url/address/tags/lat/lng
    """
    async with async_session_factory() as db:
        f = (await db.execute(
            select(Food).where(Food.id == food_id)
        )).scalars().first()

    if not f:
        return None

    tags = f.tags if isinstance(f.tags, list) else []
    return {
        "food_id": f.id,
        "name": f.name,
        "type": f.type,
        "description": f.description or "",
        "price_range": f.price_range or "",
        "image_url": f.image_url or "",
        "address": f.address or "",
        "tags": tags,
        "lat": float(f.latitude) if f.latitude else None,
        "lng": float(f.longitude) if f.longitude else None,
    }


# ═══════════════════════════════════════════
# Hotel Tools (3)
# ═══════════════════════════════════════════

@tool
async def search_hotels_by_location(
    lat: float,
    lng: float,
    radius_km: float = 3.0,
    limit: int = 10,
) -> list[dict]:
    """搜索指定坐标周边的酒店。

    参数：
        lat: 纬度 (如 23.357)
        lng: 经度 (如 116.672)
        radius_km: 搜索半径(公里)，默认 3.0
        limit: 最多返回条数，默认 10

    返回：周边酒店列表，含 hotel_id/name/region/stars/price_min/price_max/distance_km
    """
    async with async_session_factory() as db:
        result = await db.execute(
            select(Hotel).where(
                Hotel.latitude.isnot(None),
                Hotel.longitude.isnot(None),
            )
        )
        hotels = result.scalars().all()

    nearby = []
    for h in hotels:
        d = haversine(lat, lng, float(h.latitude), float(h.longitude))
        if d <= radius_km:
            tags = h.tags if isinstance(h.tags, list) else []
            nearby.append({
                "hotel_id": h.id,
                "name": h.name,
                "region": h.region or "",
                "stars": h.stars,
                "price_min": h.price_min or 0,
                "price_max": h.price_max or 0,
                "distance_km": round(d, 2),
                "address": h.address or "",
                "tags": tags,
            })

    nearby.sort(key=lambda x: x["distance_km"])
    return nearby[:limit]


@tool
async def search_hotels_by_stars(
    min_stars: int = 3,
    max_stars: int = 5,
    limit: int = 20,
) -> list[dict]:
    """按星级范围筛选酒店。

    参数：
        min_stars: 最低星级 (1-5)，默认 3
        max_stars: 最高星级 (1-5)，默认 5
        limit: 最多返回条数，默认 20

    返回：符合星级范围的酒店列表，含 hotel_id/name/region/stars/price_min/price_max/address
    """
    async with async_session_factory() as db:
        result = await db.execute(
            select(Hotel).where(
                Hotel.stars >= min_stars,
                Hotel.stars <= max_stars,
            ).limit(limit)
        )
        hotels = result.scalars().all()

    items = []
    for h in hotels:
        tags = h.tags if isinstance(h.tags, list) else []
        items.append({
            "hotel_id": h.id,
            "name": h.name,
            "region": h.region or "",
            "stars": h.stars,
            "price_min": h.price_min or 0,
            "price_max": h.price_max or 0,
            "address": h.address or "",
            "tags": tags,
            "lat": float(h.latitude) if h.latitude else None,
            "lng": float(h.longitude) if h.longitude else None,
        })

    items.sort(key=lambda x: (-x["stars"], x["price_min"]))
    return items


@tool
async def get_hotel_detail(hotel_id: int) -> Optional[dict]:
    """获取单条酒店的详细信息。

    参数：
        hotel_id: 酒店 ID

    返回：酒店详情，含 name/region/address/stars/price_min/price_max/image_url/tags/description
    """
    async with async_session_factory() as db:
        h = (await db.execute(
            select(Hotel).where(Hotel.id == hotel_id)
        )).scalars().first()

    if not h:
        return None

    tags = h.tags if isinstance(h.tags, list) else []
    return {
        "hotel_id": h.id,
        "name": h.name,
        "region": h.region or "",
        "address": h.address or "",
        "stars": h.stars,
        "price_min": h.price_min or 0,
        "price_max": h.price_max or 0,
        "image_url": h.image_url or "",
        "tags": tags,
        "description": h.description or "",
        "lat": float(h.latitude) if h.latitude else None,
        "lng": float(h.longitude) if h.longitude else None,
    }


# ═══════════════════════════════════════════
# Tool 集合导出
# ═══════════════════════════════════════════

FOOD_TOOLS = [search_foods_by_location, search_foods_by_type, get_food_detail]
HOTEL_TOOLS = [search_hotels_by_location, search_hotels_by_stars, get_hotel_detail]
ALL_TOOLS = FOOD_TOOLS + HOTEL_TOOLS
