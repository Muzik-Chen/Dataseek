"""数据大屏路由 — 天气/人流/平台概览。"""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.dashboard import WeatherRecord, CrowdRecord, CrowdLocation
from models.user import User
from models.food import Food
from models.heritage import Heritage
from models.community import CommunityPost
from models.chat import ChatMessage
from schemas.dashboard import (
    WeatherOut, CrowdOut, CrowdGeoOut,
    WeatherGeoOut, WeatherRouteOut, DashboardOverview,
)
from utils.response import success, paginated
from utils.geo import haversine, find_nearest_city, CITY_COORDS

router = APIRouter(prefix="/dashboard", tags=["数据大屏"])


@router.get("/weather")
async def get_weather(
    region: str | None = None,
    limit: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """获取天气数据（最近 N 条）。"""
    q = select(WeatherRecord).order_by(desc(WeatherRecord.record_time))
    if region:
        q = q.where(WeatherRecord.region == region)
    q = q.limit(limit)
    rows = (await db.execute(q)).scalars().all()
    items = [WeatherOut.model_validate(r).model_dump() for r in rows]
    return success(items)


@router.get("/crowd")
async def get_crowd(
    region: str | None = None,
    limit: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """获取人流数据（最近 N 条）。"""
    q = select(CrowdRecord).order_by(desc(CrowdRecord.record_time))
    if region:
        q = q.where(CrowdRecord.region == region)
    q = q.limit(limit)
    rows = (await db.execute(q)).scalars().all()
    items = [CrowdOut.model_validate(r).model_dump() for r in rows]
    return success(items)


@router.get("/crowd/history")
async def get_crowd_history(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    region: str | None = Query(None, description="区域筛选（汕头/潮州/揭阳/汕尾）"),
    db: AsyncSession = Depends(get_db),
):
    """按天聚合人流趋势 — 返回每日平均/最高人流等级和总预估人数。"""
    where_clause = "WHERE record_time >= DATE_SUB(CURDATE(), INTERVAL :days DAY)"
    params = {"days": days}
    if region:
        where_clause += " AND region = :region"
        params["region"] = region

    sql = text(f"""
        SELECT
            DATE(record_time) AS date,
            ROUND(AVG(crowd_level), 1) AS avg_level,
            MAX(crowd_level) AS max_level,
            SUM(estimated_count) AS total_count
        FROM crowd_records
        {where_clause}
        GROUP BY DATE(record_time)
        ORDER BY date ASC
    """)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    return success([
        {
            "date": str(r[0]),
            "avg_level": float(r[1]) if r[1] is not None else 0.0,
            "max_level": r[2] or 0,
            "total_count": r[3] or 0,
        }
        for r in rows
    ])


@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db)):
    """获取数据大屏概览数据。"""
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_foods = (await db.execute(select(func.count(Food.id)))).scalar() or 0
    total_heritages = (await db.execute(select(func.count(Heritage.id)))).scalar() or 0
    total_posts = (await db.execute(select(func.count(CommunityPost.id)))).scalar() or 0
    today_chats = (await db.execute(
        select(func.count(ChatMessage.id)).where(
            func.date(ChatMessage.created_at) == func.current_date()
        )
    )).scalar() or 0

    # 热门区域人流
    crowd_rows = (await db.execute(
        select(
            CrowdRecord.region,
            CrowdRecord.location_name,
            CrowdRecord.crowd_level,
        ).order_by(desc(CrowdRecord.crowd_level)).limit(10)
    )).all()

    hot_regions = [
        {"region": r[0], "location_name": r[1], "crowd_level": r[2]}
        for r in crowd_rows
    ]

    # 最新天气
    weather_rows = (await db.execute(
        select(WeatherRecord.region, WeatherRecord.temperature).order_by(
            desc(WeatherRecord.record_time)
        ).limit(10)
    )).all()

    # 合并天气到区域
    weather_map = {r[0]: float(r[1]) for r in weather_rows}
    for item in hot_regions:
        item["temperature"] = weather_map.get(item["region"], 0)

    return success(DashboardOverview(
        total_users=total_users,
        total_foods=total_foods,
        total_heritages=total_heritages,
        total_posts=total_posts,
        today_chats=today_chats,
        active_users_today=0,  # 需要埋点数据
        hot_regions=hot_regions,
    ).model_dump())


# ── 地图坐标查询端点 ──


@router.get("/crowd/geo")
async def get_crowd_geo(
    region: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = Query(None, ge=0.5, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    获取带经纬度的人流数据（供地图使用）。
    支持按 region 筛选或按坐标+半径筛选。

    返回 crowd_locations 的固定坐标 + 最新 crowd_records 的人流等级。
    """
    # 查询所有监测点坐标
    loc_q = select(CrowdLocation)
    if region:
        loc_q = loc_q.where(CrowdLocation.region == region)
    all_locations = (await db.execute(loc_q)).scalars().all()

    # 查询最新一批人流记录
    latest_time = (await db.execute(
        select(func.max(CrowdRecord.record_time))
    )).scalar() or None

    crowd_map: dict[str, CrowdRecord] = {}
    if latest_time:
        cr_rows = (await db.execute(
            select(CrowdRecord).where(CrowdRecord.record_time == latest_time)
        )).scalars().all()
        crowd_map = {r.location_name: r for r in cr_rows}

    items = []
    for loc in all_locations:
        # 按坐标范围筛选
        if lat is not None and lng is not None:
            dist = haversine(lat, lng, float(loc.latitude), float(loc.longitude))
            if radius_km and dist > radius_km:
                continue
        else:
            dist = 0.0

        crowd = crowd_map.get(loc.location_name)
        items.append({
            "id": loc.id,
            "region": loc.region,
            "location_name": loc.location_name,
            "latitude": float(loc.latitude),
            "longitude": float(loc.longitude),
            "crowd_level": crowd.crowd_level if crowd else 1,
            "estimated_count": crowd.estimated_count if crowd else 0,
            "base_capacity": loc.base_capacity,
            "record_time": crowd.record_time.isoformat() if crowd and crowd.record_time else None,
        })

    return success(items)


@router.get("/weather/geo")
async def get_weather_geo(
    lat: float = Query(...),
    lng: float = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    根据坐标返回最近城市的天气（供地图标记点使用）。
    使用 Haversine 公式找到最近的城市 → 返回该城市最新天气记录。
    """
    city, dist = find_nearest_city(lat, lng)

    latest_weather = (await db.execute(
        select(WeatherRecord)
        .where(WeatherRecord.region == city)
        .order_by(desc(WeatherRecord.record_time))
        .limit(1)
    )).scalars().first()

    if not latest_weather:
        return success({
            "region": city,
            "city": city,
            "temperature": 28.0,
            "humidity": 70,
            "weather_desc": "多云",
            "wind_level": 2,
            "distance_km": dist,
            "record_time": None,
        })

    return success({
        "region": city,
        "city": city,
        "temperature": float(latest_weather.temperature),
        "humidity": latest_weather.humidity,
        "weather_desc": latest_weather.weather_desc,
        "wind_level": latest_weather.wind_level,
        "distance_km": dist,
        "record_time": latest_weather.record_time.isoformat(),
    })


@router.get("/weather/route")
async def get_weather_route(
    waypoints: str = Query(..., description="逗号分隔经纬度: lat1,lng1;lat2,lng2;..."),
    db: AsyncSession = Depends(get_db),
):
    """
    接收一组路线坐标点，返回沿途天气摘要。
    每段取最近城市的最新天气，去重后返回。

    示例: GET /dashboard/weather/route?waypoints=23.35,116.68;23.67,116.65;23.55,116.37
    """
    points = []
    for part in waypoints.split(";"):
        part = part.strip()
        if not part:
            continue
        parts = part.split(",")
        if len(parts) == 2:
            try:
                points.append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue

    if not points:
        return success({"waypoints": [], "summary": "无有效坐标"})

    # 每段找最近城市 → 去重
    city_weather = {}
    waypoint_results = []
    for lat, lng in points:
        city, dist = find_nearest_city(lat, lng)
        if city not in city_weather:
            w = (await db.execute(
                select(WeatherRecord)
                .where(WeatherRecord.region == city)
                .order_by(desc(WeatherRecord.record_time))
                .limit(1)
            )).scalars().first()
            city_weather[city] = w

        w = city_weather[city]
        waypoint_results.append({
            "lat": lat,
            "lng": lng,
            "city": city,
            "distance_to_city_km": dist,
            "temperature": float(w.temperature) if w else 28.0,
            "weather_desc": w.weather_desc if w else "多云",
            "humidity": w.humidity if w else 70,
            "wind_level": w.wind_level if w else 2,
        })

    # 生成摘要
    unique_cities = list(city_weather.keys())
    summary_parts = []
    for city in unique_cities:
        w = city_weather[city]
        if w:
            summary_parts.append(f"{city}: {w.weather_desc} {float(w.temperature):.0f}°C")
        else:
            summary_parts.append(f"{city}: 多云 28°C")
    summary = " | ".join(summary_parts)

    return success({
        "waypoints": waypoint_results,
        "summary": summary,
    })
