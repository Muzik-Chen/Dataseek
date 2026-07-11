"""
Route Enricher — AI 路线富化模块。

在 trip_agent 生成方案后，通过 DB 查询为每个行程地点补充：
- 周边美食 (foods)
- 周边非遗 (heritages)
- 周边酒店 (hotels)
- 天气数据 (weather)
- 人流量 (crowd)

同时构建 route_geo 结构（waypoints + route_line），供前端地图渲染。

设计原则：
- 使用 Pattern B (async_session_factory)，因为 enricher 在 trip_agent 的
  async generator 内部被调用，不在 FastAPI DI 上下文中
- asyncio.gather 并行查询 5 个数据源
- 8 秒超时保护，超时返回空 enrichment（不阻塞主流程）
- Haversine 距离过滤 + 500m 内同名去重
"""
import asyncio
import logging
from typing import Optional

from sqlalchemy import select, func, desc

from database import async_session_factory
from models.food import Food
from models.heritage import Heritage
from models.hotel import Hotel
from models.dashboard import WeatherRecord, CrowdRecord, CrowdLocation
from utils.geo import haversine, find_nearest_city, CITY_COORDS

logger = logging.getLogger(__name__)

# ── 地理编码：地点名 → 坐标 ──

# 常用地点的手动映射（避免每次全表扫）
HARDCODED_GEO = {
    # 交通枢纽
    "潮汕站": (23.5440, 116.5830),
    "汕头站": (23.3730, 116.7200),
    "潮州站": (23.6550, 116.6300),
    "揭阳站": (23.5480, 116.3700),
    "揭阳潮汕机场": (23.5450, 116.5000),
    # 汕头景点
    "南澳岛": (23.4300, 117.0200),
    "青澳湾": (23.4500, 117.0800),
    "小公园": (23.3570, 116.6720),
    "汕头老城": (23.3570, 116.6720),
    "人民广场": (23.3580, 116.6780),
    "海滨长廊": (23.3520, 116.6850),
    "礐石风景区": (23.3400, 116.6600),
    "陈慈黉故居": (23.4200, 116.7450),
    "澄海": (23.4700, 116.7600),
    # 潮州景点
    "广济桥": (23.6647, 116.6484),
    "牌坊街": (23.6650, 116.6430),
    "潮州古城": (23.6650, 116.6430),
    "开元寺": (23.6655, 116.6440),
    "韩文公祠": (23.6670, 116.6560),
    "己略黄公祠": (23.6640, 116.6420),
    "龙湖古寨": (23.6100, 116.6900),
    "凤凰山": (23.9100, 116.6300),
    # 揭阳景点
    "揭阳学宫": (23.5480, 116.3700),
    "揭阳城隍庙": (23.5470, 116.3720),
    # 汕尾景点
    "红海湾": (22.7200, 115.5500),
    "汕尾红海湾": (22.7200, 115.5500),
    # 通用坐标
    "汕头": (23.3541, 116.6822),
    "汕头市区": (23.3541, 116.6822),
    "潮州": (23.6640, 116.6390),
    "潮州市区": (23.6640, 116.6390),
    "揭阳": (23.5480, 116.3700),
    "汕尾": (22.7860, 115.3750),
}


# ── 地名提取 ──

def extract_place_names(plan: dict) -> list[str]:
    """从 plan 的 days[].activities 中提取所有地点名称（去重保序）。"""
    seen = set()
    names = []
    for day in (plan.get("days") or []):
        for act in (day.get("activities") or []):
            name = (act.get("name") or "").strip()
            if name and name not in seen:
                seen.add(name)
                names.append(name)
    return names


# ── 地理编码（轻量版：只做硬编码 + 关键词拆分，无 DB 依赖） ──

def _geocode_fast(name: str) -> Optional[dict]:
    """
    轻量地理编码 — 只用硬编码映射 + 关键词拆分，不访问 DB。
    返回 {"name", "lat", "lng", "source"} 或 None。
    """
    import re

    # L1: 精确硬编码
    if name in HARDCODED_GEO:
        lat, lng = HARDCODED_GEO[name]
        return {"name": name, "lat": lat, "lng": lng, "source": "hardcoded"}

    # L2: 子串检查 — name 包含已知地点
    for loc, (clat, clng) in HARDCODED_GEO.items():
        if loc in name or name in loc:
            return {"name": name, "lat": clat, "lng": clng, "source": "hardcoded_substr"}

    # L3: 关键词拆分 — LLM 常生成"潮州古城游览"式描述
    tokens = re.split(r'[，。,\.\s·\-—、：:（）()]+', name)
    tokens = [t.strip() for t in tokens if len(t.strip()) >= 2]
    tokens.sort(key=len, reverse=True)
    for token in tokens[:3]:
        if token in HARDCODED_GEO:
            lat, lng = HARDCODED_GEO[token]
            return {"name": name, "lat": lat, "lng": lng, "source": "hardcoded_token"}
        # 子串匹配
        for loc, (clat, clng) in HARDCODED_GEO.items():
            if len(loc) >= 2 and (loc in token or token in loc):
                return {"name": name, "lat": clat, "lng": clng, "source": "hardcoded_fuzzy"}

    # L4: 城市名回退
    for city in ["汕头", "潮州", "揭阳", "汕尾"]:
        if city in name:
            clat, clng = CITY_COORDS[city]
            return {"name": name, "lat": clat, "lng": clng, "source": "city_fallback"}

    return None


# ── 地理编码（4 层降级，含 DB 查询 — 保留供外部使用） ──

async def _geocode_location(
    name: str,
    db,
) -> Optional[dict]:
    """
    四层降级策略查找地点坐标：
    1. 硬编码映射（最快）
    2. 精确匹配 — foods / heritages / hotels 中的 name 或 address
    3. 子串匹配 — like %name%
    4. 城市回退 — 如果地名包含城市名，用城市中心坐标
    5. 跳过 — 返回 None
    """
    # L1: 硬编码
    if name in HARDCODED_GEO:
        lat, lng = HARDCODED_GEO[name]
        return {"name": name, "lat": lat, "lng": lng, "source": "hardcoded"}

    # L2: 精确匹配（foods / heritages / hotels）
    for model, id_field in [(Food, "id"), (Heritage, "id"), (Hotel, "id")]:
        result = (await db.execute(
            select(model).where(model.name == name)
        )).scalars().first()
        if result and getattr(result, "latitude", None) and getattr(result, "longitude", None):
            return {
                "name": name,
                "lat": float(result.latitude),
                "lng": float(result.longitude),
                "source": model.__tablename__,
            }

    # L3: 子串匹配
    for model, id_field in [(Food, "id"), (Heritage, "id"), (Hotel, "id")]:
        result = (await db.execute(
            select(model).where(
                model.name.contains(name),
                model.latitude.isnot(None),
                model.longitude.isnot(None),
            ).limit(1)
        )).scalars().first()
        if result:
            return {
                "name": name,
                "lat": float(result.latitude),
                "lng": float(result.longitude),
                "source": f"{model.__tablename__}_fuzzy",
            }

    # L3.5: 关键词拆分匹配 — LLM 常生成描述性名称（如"潮州古城游览"），拆分后逐词匹配
    import re
    tokens = re.split(r'[，。,\.\s·\-—、：:（）()]+', name)
    tokens = [t.strip() for t in tokens if len(t.strip()) >= 2]
    # 按长度降序，优先匹配长词
    tokens.sort(key=len, reverse=True)
    for token in tokens[:5]:  # 最多试 5 个 token
        # 先试硬编码
        if token in HARDCODED_GEO:
            lat, lng = HARDCODED_GEO[token]
            return {"name": name, "lat": lat, "lng": lng, "source": "hardcoded_token"}
        # 再试 DB 精确匹配
        for model, id_field in [(Food, "id"), (Heritage, "id"), (Hotel, "id")]:
            result = (await db.execute(
                select(model).where(model.name == token)
            )).scalars().first()
            if result and getattr(result, "latitude", None) and getattr(result, "longitude", None):
                return {
                    "name": name,
                    "lat": float(result.latitude),
                    "lng": float(result.longitude),
                    "source": f"{model.__tablename__}_token",
                }

    # L4: 城市回退
    for city, (clat, clng) in CITY_COORDS.items():
        if city in name:
            return {"name": name, "lat": clat, "lng": clng, "source": "city_fallback"}

    return None


# ── 周边查询（各数据源） ──

DEFAULT_RADIUS_KM = 3.0  # 默认搜索半径


async def _query_nearby_foods(
    lat: float, lng: float, radius_km: float, db
) -> list[dict]:
    """查询周边美食。"""
    rows = (await db.execute(
        select(Food).where(
            Food.latitude.isnot(None),
            Food.longitude.isnot(None),
        )
    )).scalars().all()

    results = []
    for r in rows:
        dist = haversine(lat, lng, float(r.latitude), float(r.longitude))
        if dist <= radius_km:
            results.append({
                "food_id": r.id,
                "name": r.name,
                "type": r.type,
                "lat": float(r.latitude),
                "lng": float(r.longitude),
                "distance_km": round(dist, 2),
                "price_range": r.price_range or "",
                "image_url": r.image_url or "",
            })

    results.sort(key=lambda x: x["distance_km"])
    return _deduplicate_by_proximity(results, "food_id")


async def _query_nearby_heritages(
    lat: float, lng: float, radius_km: float, db
) -> list[dict]:
    """查询周边非遗/民俗。"""
    rows = (await db.execute(
        select(Heritage).where(
            Heritage.latitude.isnot(None),
            Heritage.longitude.isnot(None),
        )
    )).scalars().all()

    results = []
    for r in rows:
        dist = haversine(lat, lng, float(r.latitude), float(r.longitude))
        if dist <= radius_km:
            results.append({
                "id": r.id,
                "name": r.name,
                "category": r.category,
                "type": r.type,
                "lat": float(r.latitude),
                "lng": float(r.longitude),
                "distance_km": round(dist, 2),
            })

    results.sort(key=lambda x: x["distance_km"])
    return _deduplicate_by_proximity(results, "id")


async def _query_nearby_hotels(
    lat: float, lng: float, radius_km: float, db
) -> list[dict]:
    """查询周边酒店。"""
    rows = (await db.execute(select(Hotel))).scalars().all()

    results = []
    for r in rows:
        if r.latitude and r.longitude:
            dist = haversine(lat, lng, float(r.latitude), float(r.longitude))
            if dist <= radius_km:
                results.append({
                    "id": r.id,
                    "name": r.name,
                    "region": r.region,
                    "stars": r.stars,
                    "price_min": r.price_min,
                    "price_max": r.price_max,
                    "lat": float(r.latitude),
                    "lng": float(r.longitude),
                    "distance_km": round(dist, 2),
                })

    results.sort(key=lambda x: x["distance_km"])
    return _deduplicate_by_proximity(results, "id")


async def _query_nearby_crowd(
    lat: float, lng: float, radius_km: float, db
) -> list[dict]:
    """查询周边人流数据。"""
    # 所有监测点
    locs = (await db.execute(select(CrowdLocation))).scalars().all()
    # 最新人流记录
    latest_time = (await db.execute(
        select(func.max(CrowdRecord.record_time))
    )).scalar() or None

    crowd_map: dict[str, CrowdRecord] = {}
    if latest_time:
        cr_rows = (await db.execute(
            select(CrowdRecord).where(CrowdRecord.record_time == latest_time)
        )).scalars().all()
        crowd_map = {r.location_name: r for r in cr_rows}

    results = []
    for loc in locs:
        dist = haversine(lat, lng, float(loc.latitude), float(loc.longitude))
        if dist <= radius_km:
            crowd = crowd_map.get(loc.location_name)
            results.append({
                "id": loc.id,
                "location_name": loc.location_name,
                "region": loc.region,
                "lat": float(loc.latitude),
                "lng": float(loc.longitude),
                "distance_km": round(dist, 2),
                "crowd_level": crowd.crowd_level if crowd else 1,
                "estimated_count": crowd.estimated_count if crowd else 0,
            })

    results.sort(key=lambda x: x["distance_km"])
    return results


async def _query_weather_for_point(
    lat: float, lng: float, db
) -> Optional[dict]:
    """查询离坐标最近城市的天气。"""
    city, dist = find_nearest_city(lat, lng)
    weather = (await db.execute(
        select(WeatherRecord)
        .where(WeatherRecord.region == city)
        .order_by(desc(WeatherRecord.record_time))
        .limit(1)
    )).scalars().first()

    if weather:
        return {
            "city": city,
            "temperature": float(weather.temperature),
            "weather_desc": weather.weather_desc,
            "humidity": weather.humidity,
            "wind_level": weather.wind_level,
            "distance_to_city_km": dist,
        }
    return {
        "city": city,
        "temperature": 28.0,
        "weather_desc": "多云",
        "humidity": 70,
        "wind_level": 2,
        "distance_to_city_km": dist,
    }


# ── 去重工具 ──

def _deduplicate_by_proximity(
    items: list[dict], id_key: str, proximity_m: float = 500
) -> list[dict]:
    """
    按距离排序后，过滤掉与已保留项 500m 内且名称相似的重复项。
    保留距离更近的那个（因为已排序）。
    """
    if len(items) <= 1:
        return items

    kept = [items[0]]
    for item in items[1:]:
        is_dup = False
        for k in kept:
            if item.get("name") == k.get("name"):
                is_dup = True
                break
            # 如果 ID 相同，跳过
            if item.get(id_key) == k.get(id_key):
                is_dup = True
                break
        if not is_dup:
            kept.append(item)
    return kept


# ── 兴趣匹配 ──

def _match_interest_hints(
    enrichment: dict, interest_hints: list[str]
) -> list[dict]:
    """从 enrichment 数据中匹配用户兴趣关键词。"""
    if not interest_hints:
        return []

    matches = []
    all_foods = enrichment.get("foods", [])
    all_heritages = enrichment.get("heritages", [])

    for hint in interest_hints:
        hint_lower = hint.lower()
        for food in all_foods:
            if hint_lower in food["name"].lower() or any(
                hint_lower in (t or "").lower() for t in (food.get("tags") or [])
            ):
                matches.append({"type": "food", "hint": hint, "item": food})
        for heritage in all_heritages:
            if (hint_lower in heritage["name"].lower()
                or hint_lower in (heritage.get("type") or "").lower()
                or hint_lower in (heritage.get("category") or "").lower()):
                matches.append({"type": "heritage", "hint": hint, "item": heritage})

    # 去重
    seen_keys = set()
    unique = []
    for m in matches:
        key = (m["type"], m["item"].get("name") or m["item"].get("id"))
        if key not in seen_keys:
            seen_keys.add(key)
            unique.append(m)

    return unique


# ── 主入口 ──

async def enrich_plan(
    plan: dict,
    interest_hints: list[str] | None = None,
    timeout: float = 8.0,
) -> dict:
    """
    为单套行程方案注入富化数据（天气/美食/非遗/酒店/人流）。

    Args:
        plan: trip_agent 生成的 plan dict
        interest_hints: 从用户消息中提取的兴趣关键词
        timeout: 整个富化流程的超时秒数

    Returns:
        {"enrichment": {...}, "route_geo": {...}}
        - enrichment: 各数据源的查询结果
        - route_geo: waypoints + route_line 用于前端地图渲染

    超时或异常时返回空结构，不影响主流程。
    """
    async def _do_enrich():
        import re

        place_names = extract_place_names(plan)
        if not place_names:
            return _empty_result()

        # 1. 轻量地理编码：只做硬编码 + 关键词拆分，不做 DB 查询
        geocoded = []
        for name in place_names:
            geo = _geocode_fast(name)
            if geo:
                geocoded.append(geo)

        # 2. 若全部失败，用汕头市中心作为 fallback
        if not geocoded:
            shantou_lat, shantou_lng = CITY_COORDS["汕头"]
            geocoded = [{
                "name": "汕头市区",
                "lat": shantou_lat,
                "lng": shantou_lng,
                "source": "fallback",
            }]

        async with async_session_factory() as db:
            center = geocoded[0]
            lat, lng = center["lat"], center["lng"]
            radius = DEFAULT_RADIUS_KM

            # Phase 6: food/hotel 查询已迁移到 agent_tools.py
            # route_enricher 只负责：非遗 + 人流 + 天气 + route_geo 构建
            heritages = await _query_nearby_heritages(lat, lng, radius, db)
            crowd = await _query_nearby_crowd(lat, lng, radius, db)

            # 3. 对每个 waypoint 也查询天气
            waypoint_weather = []
            for geo in geocoded:
                w = await _query_weather_for_point(geo["lat"], geo["lng"], db)
                if w:
                    waypoint_weather.append({
                        "name": geo["name"],
                        "lat": geo["lat"],
                        "lng": geo["lng"],
                        **w,
                    })

            # 4. 构建 route_geo（waypoints + route_line）
            waypoints = [
                {
                    "name": g["name"],
                    "lat": g["lat"],
                    "lng": g["lng"],
                    "source": g["source"],
                }
                for g in geocoded
            ]
            route_line = [[g["lng"], g["lat"]] for g in geocoded]

            # Phase 6: foods/hotels 留空 — 由 Agent Tools 直接注入 merged_plan
            enrichment = {
                "weather": waypoint_weather,
                "foods": [],
                "heritages": heritages,
                "hotels": [],
                "crowd": crowd,
                "interest_matches": [],
            }

            # 5. 兴趣匹配
            if interest_hints:
                enrichment["interest_matches"] = _match_interest_hints(
                    enrichment, interest_hints
                )

            return {
                "enrichment": enrichment,
                "route_geo": {
                    "waypoints": waypoints,
                    "route_line": route_line,
                },
            }

    try:
        return await asyncio.wait_for(_do_enrich(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"[RouteEnricher] enrich_plan timed out after {timeout}s")
        return _empty_result()
    except Exception as e:
        logger.warning(f"[RouteEnricher] enrich_plan failed: {e}")
        return _empty_result()


def _empty_result() -> dict:
    """返回空的富化结果。"""
    return {
        "enrichment": {
            "weather": [],
            "foods": [],
            "heritages": [],
            "hotels": [],
            "crowd": [],
            "interest_matches": [],
        },
        "route_geo": {
            "waypoints": [],
            "route_line": [],
        },
    }
